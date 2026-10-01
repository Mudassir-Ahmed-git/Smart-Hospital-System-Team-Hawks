"""Glue between the database and the pure AI modules."""
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai import chatbot, predictor, recommender
from app.config import settings
from app.models.capacity_history import CapacityHistory
from app.models.emergency import EmergencyRequest
from app.models.referral import Referral
from app.services import hospital_service as hs
from app.utils.helpers import eta_minutes


def _pending_by_hospital(db: Session, bed_type: str) -> dict[int, int]:
    counts: dict[int, int] = {}
    for hid, n in db.execute(select(Referral.to_hospital, func.count()).where(
            Referral.status == "Pending", Referral.bed_type == bed_type).group_by(Referral.to_hospital)):
        counts[hid] = counts.get(hid, 0) + n
    for hid, n in db.execute(select(EmergencyRequest.hospital_id, func.count()).where(
            EmergencyRequest.status == "Pending", EmergencyRequest.required_service == bed_type,
            EmergencyRequest.hospital_id.is_not(None)).group_by(EmergencyRequest.hospital_id)):
        counts[hid] = counts.get(hid, 0) + n
    return counts


def recommend(db: Session, bed_type: str, priority: str = "Urgent", lat: float | None = None,
              lng: float | None = None, specialty: str | None = None, limit: int = 3) -> list[dict]:
    """Ranked hospital recommendations with score breakdown and a human-readable reason."""
    hospitals = hs.list_hospitals(db, lat, lng)
    pending = _pending_by_hospital(db, bed_type)
    candidates = []
    for h in hospitals:
        b = h["beds"]
        mine = b.get(bed_type, {"total": 0, "available": 0})
        candidates.append(recommender.Candidate(
            hospital_id=h["id"], name=h["name"], area=h["area"], distance_km=h["distanceKm"],
            total=mine["total"], available=mine["available"], emergency_status=h["emergencyStatus"],
            emergency_beds_free=b["Emergency"]["available"],
            critical_care_free=b["ICU"]["available"] + b["Ventilator"]["available"],
            pending_requests=pending.get(h["id"], 0), specialties=h["specialties"],
        ))
    ranked = recommender.rank(candidates, priority, settings.MAX_SEARCH_RADIUS_KM, specialty)
    if not ranked:
        return []
    nearest_id = min((r["candidate"] for r in ranked), key=lambda c: c.distance_km).hospital_id
    most_id = max((r["candidate"] for r in ranked), key=lambda c: c.available).hospital_id
    out = []
    for i, r in enumerate(ranked[:limit]):
        c = r["candidate"]
        out.append({
            "rank": i + 1, "hospitalId": c.hospital_id, "hospital": c.name, "area": c.area,
            "bedType": bed_type, "available": c.available, "total": c.total,
            "distanceKm": c.distance_km, "etaMinutes": eta_minutes(c.distance_km),
            "emergencyStatus": c.emergency_status, "estimatedWaitMinutes": recommender.estimated_wait_minutes(c.pending_requests),
            "score": r["score"], "scoreBreakdown": r["breakdown"],
            "weights": recommender.WEIGHTS,
            "reason": recommender.explain(r, bed_type, c.hospital_id == nearest_id, c.hospital_id == most_id),
        })
    return out


def best_hospital(db: Session, bed_type: str, priority: str, lat=None, lng=None) -> dict | None:
    recs = recommend(db, bed_type, priority, lat, lng, limit=1)
    return recs[0] if recs else None


# ----------------------------------------------------------------------------- forecasting
_COL = {"ICU": ("icu_usage", "icu_total"), "General": ("general_occupied", "general_total"),
        "Emergency": ("emergency_occupied", "emergency_total")}


def predict(db: Session, hospital_id: int | None = None, bed_type: str = "ICU", horizon: int = 3) -> dict:
    if hospital_id:
        hs.get_hospital_or_404(db, hospital_id)
    if bed_type == "Overall":
        occ_col, tot_col = "occupied_beds", "total_beds"
    elif bed_type in _COL:
        occ_col, tot_col = _COL[bed_type]
    else:
        occ_col, tot_col = _COL["ICU"]
        bed_type = "ICU"
    q = select(CapacityHistory.date, getattr(CapacityHistory, occ_col), getattr(CapacityHistory, tot_col),
               CapacityHistory.hospital_id)
    if hospital_id:
        q = q.where(CapacityHistory.hospital_id == hospital_id)
    rows = db.execute(q).all()
    df = pd.DataFrame(rows, columns=["date", "occ", "total", "hospital_id"])
    if not df.empty:
        # network-wide: sum occupied/total per timestamp bucket, then convert to %
        df["day"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
        g = df.groupby("day", as_index=False)[["occ", "total"]].sum()
        g = g[g["total"] > 0]
        g["occupancy"] = g["occ"] / g["total"] * 100
        hist = g.rename(columns={"day": "date"})[["date", "occupancy"]]
    else:
        hist = pd.DataFrame(columns=["date", "occupancy"])
    f = predictor.forecast_occupancy(hist, horizon)
    label = "ICU" if bed_type == "ICU" else bed_type
    message, risk = predictor.describe(label, f)
    return {"hospitalId": hospital_id, "bedType": bed_type, "message": message, "riskLevel": risk,
            "currentOccupancyPct": f.get("current"), "predictedTomorrowPct": f.get("tomorrow"),
            "changePct": f.get("changePct"), "forecast": f.get("forecast", []), "uncertainty": f.get("uncertainty"),
            "model": "ridge-regression(trend + weekly seasonality)", "daysOfHistory": f.get("daysOfHistory", 0)}


# ----------------------------------------------------------------------------- chatbot
def chat(db: Session, message: str, lat: float | None = None, lng: float | None = None) -> dict:
    parsed = chatbot.detect(message)
    intent, bed_type = parsed["intent"], parsed["bed_type"]
    if intent == "greeting":
        return {"reply": chatbot.HELP_TEXT, "intent": intent}
    if intent == "alerts":
        alerts = hs.detect_alerts(db)
        if not alerts:
            return {"reply": "No capacity alerts right now. All hospitals are within normal limits.", "intent": intent}
        top = " ".join(f"{a['hospital']} - {a['message']}" for a in alerts[:3])
        return {"reply": f"{len(alerts)} active alert{'s' if len(alerts) != 1 else ''}. {top}", "intent": intent}
    if intent == "forecast":
        p = predict(db, None, bed_type if bed_type in ("ICU", "General", "Emergency") else "ICU")
        return {"reply": f"Network forecast: {p['message']}", "intent": intent, "bedType": p["bedType"]}
    if intent == "nearest":
        nearest = min(hs.list_hospitals(db, lat, lng), key=lambda h: h["distanceKm"])
        return {"reply": f"The closest hospital is {nearest['name']}, {nearest['distanceKm']} km away "
                         f"(emergency {nearest['emergencyStatus']}).", "intent": intent}
    if intent == "availability":
        recs = recommend(db, bed_type, parsed["priority"], lat, lng, limit=3)
        rows = [{"hospital": r["hospital"], "available": r["available"], "distanceKm": r["distanceKm"],
                 "etaMinutes": r["etaMinutes"]} for r in recs]
        return {"reply": chatbot.reply_availability(bed_type, rows), "intent": intent, "bedType": bed_type,
                "recommendation": recs[0] if recs else None}
    return {"reply": chatbot.HELP_TEXT, "intent": "unknown"}
