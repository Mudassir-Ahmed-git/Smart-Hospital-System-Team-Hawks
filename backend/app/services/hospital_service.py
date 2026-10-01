"""Hospital queries, live capacity maths, capacity history snapshots and capacity monitoring."""
from collections import defaultdict
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.bed import Bed
from app.models.capacity_history import CapacityHistory
from app.models.emergency import EmergencyRequest
from app.models.hospital import Hospital
from app.services import notification_service as notify
from app.utils.helpers import as_utc, haversine_km, utcnow
from app.utils.validators import BED_TYPES, bed_prefix

CORE_TYPES = ("ICU", "General", "Emergency", "Ventilator")  # always present in API output (UI expects them)
SNAPSHOT_MERGE_MINUTES = 5


# ----------------------------------------------------------------------------- capacity maths
def capacity_for(db: Session, hospital_ids: list[int] | None = None) -> dict[int, dict[str, dict]]:
    """{hospital_id: {bed_type: {total, available}}} using one grouped query."""
    q = select(
        Bed.hospital_id,
        Bed.bed_type,
        func.count(Bed.bed_id),
        func.sum(case((Bed.status == "Available", 1), else_=0)),
    ).group_by(Bed.hospital_id, Bed.bed_type)
    if hospital_ids is not None:
        q = q.where(Bed.hospital_id.in_(hospital_ids))
    out: dict[int, dict[str, dict]] = defaultdict(dict)
    for hid, btype, total, avail in db.execute(q):
        out[hid][btype] = {"total": int(total), "available": int(avail or 0)}
    return out


def beds_payload(caps: dict[str, dict] | None) -> dict[str, dict]:
    caps = caps or {}
    out = {t: dict(caps.get(t, {"total": 0, "available": 0})) for t in CORE_TYPES}
    if "Operation Theater" in caps:  # only shown for hospitals that have OTs
        out["Operation Theater"] = dict(caps["Operation Theater"])
    return out


def derive_status(beds: dict[str, dict]) -> str:
    """normal | busy | critical - drives the colours on the frontend map/cards."""
    total = sum(v["total"] for v in beds.values())
    free = sum(v["available"] for v in beds.values())
    ratio = free / total if total else 0
    icu = beds.get("ICU", {"total": 0, "available": 0})
    icu_ratio = icu["available"] / icu["total"] if icu["total"] else 1
    if total and (ratio < 0.10 or (icu["total"] and icu["available"] == 0)):
        return "critical"
    if total and (ratio < 0.25 or icu_ratio < 0.15):
        return "busy"
    return "normal"


def _map_bounds(hospitals: list[Hospital]):
    lats = [h.latitude for h in hospitals]
    lngs = [h.longitude for h in hospitals]
    return (min(lats), max(lats), min(lngs), max(lngs)) if hospitals else (0, 0, 0, 0)


def _scale(v, lo, hi):
    return 50.0 if hi - lo < 1e-9 else round(12 + (v - lo) / (hi - lo) * 76, 1)


def serialize_hospital(h: Hospital, caps: dict[str, dict], lat: float, lng: float, bounds) -> dict:
    beds = beds_payload(caps)
    lo_lat, hi_lat, lo_lng, hi_lng = bounds
    return {
        "id": h.hospital_id,
        "name": h.name,
        "area": h.area,
        "address": h.address,
        "distanceKm": round(haversine_km(lat, lng, h.latitude, h.longitude), 1),
        "phone": h.contact_number,
        "latitude": h.latitude,
        "longitude": h.longitude,
        "x": _scale(h.longitude, lo_lng, hi_lng),
        "y": _scale(-h.latitude, -hi_lat, -lo_lat),  # north is up
        "specialties": h.specialties or [],
        "status": derive_status(beds),
        "emergencyStatus": h.emergency_status,
        "beds": beds,
    }


def list_hospitals(db: Session, lat: float | None = None, lng: float | None = None) -> list[dict]:
    lat = settings.DEFAULT_LATITUDE if lat is None else lat
    lng = settings.DEFAULT_LONGITUDE if lng is None else lng
    hospitals = list(db.scalars(select(Hospital).order_by(Hospital.hospital_id)))
    caps = capacity_for(db)
    bounds = _map_bounds(hospitals)
    return [serialize_hospital(h, caps.get(h.hospital_id, {}), lat, lng, bounds) for h in hospitals]


def get_hospital_or_404(db: Session, hospital_id: int) -> Hospital:
    h = db.get(Hospital, hospital_id)
    if not h:
        raise HTTPException(404, f"Hospital {hospital_id} not found")
    return h


def get_hospital_dict(db: Session, hospital_id: int, lat=None, lng=None) -> dict:
    get_hospital_or_404(db, hospital_id)
    return next(h for h in list_hospitals(db, lat, lng) if h["id"] == hospital_id)


# ----------------------------------------------------------------------------- mutations
def _next_code(db: Session, hospital_id: int, bed_type: str) -> str:
    prefix = bed_prefix(bed_type)
    codes = db.scalars(select(Bed.code).where(Bed.hospital_id == hospital_id, Bed.code.like(f"{prefix}-%")))
    nums = [int(c.split("-")[1]) for c in codes if c.split("-")[1].isdigit()]
    return f"{prefix}-{(max(nums) + 1) if nums else 1:02d}"


def add_beds(db: Session, hospital_id: int, bed_type: str, count: int, status: str = "Available") -> None:
    for _ in range(count):
        db.add(Bed(hospital_id=hospital_id, bed_type=bed_type, code=_next_code(db, hospital_id, bed_type), status=status))
        db.flush()


def create_hospital(db: Session, data) -> Hospital:
    if db.scalar(select(Hospital).where(func.lower(Hospital.name) == data.name.lower())):
        raise HTTPException(409, "A hospital with this name already exists")
    h = Hospital(
        name=data.name, address=data.address, area=data.area, latitude=data.latitude, longitude=data.longitude,
        contact_number=data.contact_number, emergency_status=data.emergency_status, specialties=data.specialties,
    )
    db.add(h)
    db.flush()
    for btype, n in data.beds.items():
        add_beds(db, h.hospital_id, btype, n)
    record_snapshot(db, h.hospital_id)
    db.commit()
    return h


def set_capacity(db: Session, hospital: Hospital, update) -> None:
    """Make the DB match what the hospital reports: {type: {available, total?}}.
    Beds are real rows, so we flip statuses (and add/remove rows if the total changed)."""
    for btype, item in update.beds.items():
        beds = list(db.scalars(select(Bed).where(Bed.hospital_id == hospital.hospital_id, Bed.bed_type == btype)
                               .order_by(Bed.bed_id).with_for_update()))
        total = item.total if item.total is not None else len(beds)
        if item.available > total:
            raise HTTPException(422, f"{btype}: available ({item.available}) cannot exceed total ({total})")

        if total > len(beds):  # grow
            add_beds(db, hospital.hospital_id, btype, total - len(beds), status="Occupied")
            beds = list(db.scalars(select(Bed).where(Bed.hospital_id == hospital.hospital_id, Bed.bed_type == btype)
                                   .order_by(Bed.bed_id)))
        elif total < len(beds):  # shrink: drop free beds first, never delete a bed with a patient
            removable = [b for b in reversed(beds) if b.status in ("Available", "Cleaning")]
            need = len(beds) - total
            if len(removable) < need:
                raise HTTPException(409, f"Cannot reduce {btype} total to {total}: too many beds are occupied/reserved")
            for b in removable[:need]:
                db.delete(b)
            db.flush()
            beds = [b for b in beds if b not in removable[:need]]

        available = [b for b in beds if b.status == "Available"]
        diff = item.available - len(available)
        if diff > 0:  # free up beds: cleaning first, then occupied (discharge), never reserved
            candidates = sorted((b for b in beds if b.status in ("Cleaning", "Occupied")), key=lambda b: b.status != "Cleaning")
            if len(candidates) < diff:
                raise HTTPException(409, f"{btype}: cannot mark {item.available} beds free - "
                                         f"{len([b for b in beds if b.status == 'Reserved'])} are reserved for incoming patients")
            for b in candidates[:diff]:
                b.status, b.patient_name = "Available", None
        elif diff < 0:  # admit: occupy the free beds
            for b in available[: -diff]:
                b.status = "Occupied"
    if update.emergency_status:
        hospital.emergency_status = update.emergency_status
    db.flush()
    record_snapshot(db, hospital.hospital_id)
    db.commit()
    notify.notify_capacity_changed(hospital.hospital_id)


# ----------------------------------------------------------------------------- history
def record_snapshot(db: Session, hospital_id: int, when=None, commit: bool = False) -> CapacityHistory:
    """Write (or refresh, if one was written a moment ago) the current capacity snapshot."""
    when = when or utcnow()
    caps = capacity_for(db, [hospital_id]).get(hospital_id, {})
    g = lambda t, k: caps.get(t, {}).get(k, 0)  # noqa: E731
    total = sum(v["total"] for v in caps.values())
    occupied = total - sum(v["available"] for v in caps.values())
    since = when - timedelta(hours=24)
    em24 = db.scalar(select(func.count(EmergencyRequest.request_id)).where(
        EmergencyRequest.hospital_id == hospital_id, EmergencyRequest.created_time >= since)) or 0
    values = dict(
        total_beds=total, occupied_beds=occupied, emergency_requests=em24,
        icu_total=g("ICU", "total"), icu_usage=g("ICU", "total") - g("ICU", "available"),
        general_total=g("General", "total"), general_occupied=g("General", "total") - g("General", "available"),
        emergency_total=g("Emergency", "total"), emergency_occupied=g("Emergency", "total") - g("Emergency", "available"),
    )
    last = db.scalar(select(CapacityHistory).where(CapacityHistory.hospital_id == hospital_id)
                     .order_by(CapacityHistory.date.desc()).limit(1))
    if last and abs((as_utc(when) - as_utc(last.date)).total_seconds()) < SNAPSHOT_MERGE_MINUTES * 60:
        for k, v in values.items():
            setattr(last, k, v)
        snap = last
    else:
        snap = CapacityHistory(hospital_id=hospital_id, date=when, **values)
        db.add(snap)
    if commit:
        db.commit()
    return snap


# ----------------------------------------------------------------------------- monitoring
def detect_alerts(db: Session, hospital_id: int | None = None) -> list[dict]:
    """Bed shortage, ICU overload, emergency spikes."""
    q = select(Hospital)
    if hospital_id:
        q = q.where(Hospital.hospital_id == hospital_id)
    hospitals = list(db.scalars(q))
    caps = capacity_for(db, [h.hospital_id for h in hospitals])
    now = utcnow()
    alerts: list[dict] = []

    for h in hospitals:
        beds = beds_payload(caps.get(h.hospital_id))
        total = sum(v["total"] for v in beds.values())
        free = sum(v["available"] for v in beds.values())
        if total and free / total < 0.15:
            sev = "critical" if free / total < 0.08 else "warning"
            alerts.append({"type": "bed_shortage", "severity": sev, "hospitalId": h.hospital_id, "hospital": h.name,
                           "message": f"Bed shortage: only {free} of {total} beds free ({free / total:.0%})."})
        icu = beds["ICU"]
        if icu["total"]:
            occ = 1 - icu["available"] / icu["total"]
            if occ >= 0.85:
                alerts.append({"type": "icu_overload", "severity": "critical" if occ >= 0.95 else "warning",
                               "hospitalId": h.hospital_id, "hospital": h.name,
                               "message": f"ICU overload: {occ:.0%} occupied ({icu['available']} of {icu['total']} free)."})
        # emergency spike: last 2h vs the hourly average of the previous 7 days
        recent = db.scalar(select(func.count(EmergencyRequest.request_id)).where(
            EmergencyRequest.hospital_id == h.hospital_id, EmergencyRequest.created_time >= now - timedelta(hours=2))) or 0
        week = db.scalar(select(func.count(EmergencyRequest.request_id)).where(
            EmergencyRequest.hospital_id == h.hospital_id,
            EmergencyRequest.created_time >= now - timedelta(days=7),
            EmergencyRequest.created_time < now - timedelta(hours=2))) or 0
        baseline_2h = week / (7 * 24) * 2
        if recent >= 3 and recent >= 2 * max(baseline_2h, 0.5):
            alerts.append({"type": "emergency_spike", "severity": "warning", "hospitalId": h.hospital_id,
                           "hospital": h.name,
                           "message": f"Emergency spike: {recent} requests in 2h vs ~{baseline_2h:.1f} normally."})
    order = {"critical": 0, "warning": 1}
    return sorted(alerts, key=lambda a: order[a["severity"]])
