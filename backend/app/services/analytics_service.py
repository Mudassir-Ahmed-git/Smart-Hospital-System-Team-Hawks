"""Dashboard numbers, chart series and weekly reports."""
from collections import Counter, defaultdict
from datetime import timedelta

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.capacity_history import CapacityHistory
from app.models.emergency import EmergencyRequest
from app.models.hospital import Hospital
from app.models.referral import Referral
from app.services import hospital_service as hs
from app.utils.helpers import as_utc, utcnow


def dashboard(db: Session, hospital_id: int | None = None) -> dict:
    ids = [hospital_id] if hospital_id else None
    hospitals = list(db.scalars(select(Hospital).where(Hospital.hospital_id == hospital_id) if hospital_id else select(Hospital)))
    caps = hs.capacity_for(db, ids)
    by_type: dict[str, dict] = {}
    for hid in (h.hospital_id for h in hospitals):
        for t, v in caps.get(hid, {}).items():
            agg = by_type.setdefault(t, {"total": 0, "available": 0})
            agg["total"] += v["total"]
            agg["available"] += v["available"]
    for v in by_type.values():
        v["occupancyPct"] = round((1 - v["available"] / v["total"]) * 100, 1) if v["total"] else 0.0
    total = sum(v["total"] for v in by_type.values())
    avail = sum(v["available"] for v in by_type.values())
    icu = by_type.get("ICU", {"total": 0, "available": 0})

    now = utcnow()
    em_q = select(func.count(EmergencyRequest.request_id))
    ref_q = select(func.count(Referral.referral_id)).where(Referral.status == "Pending")
    if hospital_id:
        em_q = em_q.where(EmergencyRequest.hospital_id == hospital_id)
        ref_q = ref_q.where(Referral.to_hospital == hospital_id)
    return {
        "totalHospitals": len(hospitals), "totalBeds": total, "availableBeds": avail,
        "icuTotal": icu["total"], "icuAvailable": icu["available"],
        "icuOccupancyPct": round((1 - icu["available"] / icu["total"]) * 100, 1) if icu["total"] else 0.0,
        "emergencyRequests": db.scalar(em_q.where(EmergencyRequest.status == "Pending")) or 0,
        "emergencyRequests24h": db.scalar(em_q.where(EmergencyRequest.created_time >= now - timedelta(hours=24))) or 0,
        "pendingReferrals": db.scalar(ref_q) or 0,
        "byType": by_type,
        "alerts": hs.detect_alerts(db, hospital_id),
    }


def capacity_chart(db: Session, hospital_id: int | None = None, days: int = 7) -> dict:
    """Chart-ready data: current per-hospital capacity + daily occupancy series for the last `days`."""
    hospitals = hs.list_hospitals(db)
    if hospital_id:
        hospitals = [h for h in hospitals if h["id"] == hospital_id]
    by_hospital = []
    for h in hospitals:
        b = h["beds"]
        total = sum(v["total"] for v in b.values())
        free = sum(v["available"] for v in b.values())
        icu = b["ICU"]
        by_hospital.append({
            "hospitalId": h["id"], "hospital": h["name"], "status": h["status"],
            "totalBeds": total, "availableBeds": free, "occupiedBeds": total - free,
            "occupancyPct": round((1 - free / total) * 100, 1) if total else 0.0,
            "icuOccupancyPct": round((1 - icu["available"] / icu["total"]) * 100, 1) if icu["total"] else 0.0,
            "beds": b,
        })
    since = utcnow() - timedelta(days=days)
    q = select(CapacityHistory).where(CapacityHistory.date >= since)
    if hospital_id:
        q = q.where(CapacityHistory.hospital_id == hospital_id)
    rows = list(db.scalars(q))
    daily: list[dict] = []
    if rows:
        df = pd.DataFrame([{
            "day": as_utc(r.date).date().isoformat(), "total": r.total_beds, "occ": r.occupied_beds,
            "icu_total": r.icu_total, "icu_occ": r.icu_usage, "em": r.emergency_requests} for r in rows])
        g = df.groupby("day").agg(total=("total", "sum"), occ=("occ", "sum"), icu_total=("icu_total", "sum"),
                                  icu_occ=("icu_occ", "sum"), em=("em", "max")).reset_index()
        for _, x in g.iterrows():
            daily.append({"date": x["day"], "occupancyPct": round(x["occ"] / x["total"] * 100, 1) if x["total"] else 0,
                          "icuOccupancyPct": round(x["icu_occ"] / x["icu_total"] * 100, 1) if x["icu_total"] else 0})
    # emergency requests per day (real counts, not the rolling 24h figure)
    eq = select(EmergencyRequest.created_time).where(EmergencyRequest.created_time >= since)
    if hospital_id:
        eq = eq.where(EmergencyRequest.hospital_id == hospital_id)
    per_day = Counter(as_utc(t).date().isoformat() for (t,) in db.execute(eq))
    for d in daily:
        d["emergencyRequests"] = per_day.get(d["date"], 0)
    return {"byHospital": by_hospital, "daily": daily}


def occupancy_trend(db: Session, hospital_id: int | None = None) -> list[dict]:
    """[{time:'08:00', ICU: 70, General: 60, Emergency: 55}] - % occupied by 4-hour slot over the last 24h.
    This is the shape the frontend's occupancy chart expects."""
    since = utcnow() - timedelta(hours=24)
    q = select(CapacityHistory).where(CapacityHistory.date >= since)
    if hospital_id:
        q = q.where(CapacityHistory.hospital_id == hospital_id)
    slots: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in db.scalars(q):
        h = (as_utc(r.date).hour // 4) * 4
        s = slots[h]
        s["icu_t"] += r.icu_total; s["icu_o"] += r.icu_usage
        s["gen_t"] += r.general_total; s["gen_o"] += r.general_occupied
        s["em_t"] += r.emergency_total; s["em_o"] += r.emergency_occupied
    pct = lambda o, t: round(o / t * 100) if t else 0  # noqa: E731
    return [{"time": f"{h:02d}:00", "ICU": pct(s["icu_o"], s["icu_t"]), "General": pct(s["gen_o"], s["gen_t"]),
             "Emergency": pct(s["em_o"], s["em_t"])} for h, s in sorted(slots.items())]


def weekly_reports(db: Session, weeks: int = 4) -> list[dict]:
    """Admissions, transfers, average response wait and peak hour per ISO week."""
    since = utcnow() - timedelta(weeks=weeks)
    refs = db.execute(select(Referral.created_at, Referral.responded_at, Referral.status, Referral.from_hospital,
                             Referral.ambulance_status).where(Referral.created_at >= since)).all()
    ems = db.execute(select(EmergencyRequest.created_time, EmergencyRequest.responded_at, EmergencyRequest.status)
                     .where(EmergencyRequest.created_time >= since)).all()
    buckets: dict[tuple, dict] = defaultdict(lambda: {"adm": 0, "tr": 0, "waits": [], "peaks": Counter()})
    def key(dt):
        iso = as_utc(dt).isocalendar()
        return (iso[0], iso[1])
    for created, responded, status, frm, amb in refs:
        b = buckets[key(created)]
        b["adm"] += status in ("Accepted", "Completed")
        b["tr"] += bool(frm or amb)
        if responded:
            b["waits"].append((as_utc(responded) - as_utc(created)).total_seconds() / 60)
        b["peaks"][as_utc(created).strftime("%a %H:00")] += 1
    for created, responded, status in ems:
        b = buckets[key(created)]
        b["adm"] += status in ("Accepted", "Admitted", "Completed")
        if responded:
            b["waits"].append((as_utc(responded) - as_utc(created)).total_seconds() / 60)
        b["peaks"][as_utc(created).strftime("%a %H:00")] += 1
    rows = []
    for (yr, wk), b in sorted(buckets.items()):
        rows.append({"period": f"Week {wk}", "admissions": int(b["adm"]), "transfers": int(b["tr"]),
                     "avgWait": f"{round(sum(b['waits']) / len(b['waits']))} min" if b["waits"] else "-",
                     "peak": b["peaks"].most_common(1)[0][0] if b["peaks"] else "-"})
    return rows
