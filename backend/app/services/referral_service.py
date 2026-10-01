"""Bed requests, referrals/transfers, emergency requests and the ambulance fleet."""
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ambulance import Ambulance
from app.models.emergency import EmergencyRequest
from app.models.hospital import Hospital
from app.models.patient import Patient
from app.models.referral import Referral
from app.models.user import User
from app.services import ai_service, bed_service
from app.services import hospital_service as hs
from app.services import notification_service as notify
from app.utils.helpers import as_utc, eta_minutes, parse_ref, ref_id, time_ago, utcnow
from app.utils.validators import AMBULANCE_STEPS, PRIORITY_RANK

REF_PREFIX, REF_OFFSET = "REF", 1000
EM_PREFIX, EM_OFFSET = "EM", 300

# Allowed referral status transitions
_TRANSITIONS = {
    "Pending": {"Accepted", "Rejected", "Cancelled"},
    "Accepted": {"Completed", "Cancelled", "Rejected"},
    "Rejected": set(), "Completed": set(), "Cancelled": set(),
}


# ----------------------------------------------------------------------------- helpers
def get_or_create_patient(db: Session, user: User | None, name: str, age: int | None, condition: str, priority: str) -> Patient:
    patient = None
    if user is not None and user.role == "patient":
        patient = db.scalar(select(Patient).where(Patient.user_id == user.id, func.lower(Patient.name) == name.lower()))
    if patient:
        patient.medical_requirement, patient.priority = condition or patient.medical_requirement, priority
        if age is not None:
            patient.age = age
    else:
        patient = Patient(user_id=user.id if user and user.role == "patient" else None, name=name, age=age,
                          medical_requirement=condition, priority=priority)
        db.add(patient)
    db.flush()
    return patient


def _names(db: Session, hospital_ids: set) -> dict[int, str]:
    ids = {i for i in hospital_ids if i}
    if not ids:
        return {}
    return {h.hospital_id: h.name for h in db.scalars(select(Hospital).where(Hospital.hospital_id.in_(ids)))}


def _patients(db: Session, ids: set) -> dict[int, Patient]:
    ids = {i for i in ids if i}
    if not ids:
        return {}
    return {p.patient_id: p for p in db.scalars(select(Patient).where(Patient.patient_id.in_(ids)))}


def _default_note(r: Referral, hospital: str) -> str:
    return {
        "Pending": "Waiting for hospital response.",
        "Accepted": "Bed reserved. Arrive within 30 minutes.",
        "Rejected": f"No {r.bed_type} beds available. Try another hospital.",
        "Completed": "Handover complete.",
        "Cancelled": "Request cancelled.",
    }[r.status]


def serialize_referrals(db: Session, rows: list[Referral]) -> list[dict]:
    names = _names(db, {r.to_hospital for r in rows} | {r.from_hospital for r in rows})
    patients = _patients(db, {r.patient_id for r in rows})
    out = []
    for r in rows:
        p = patients.get(r.patient_id)
        out.append({
            "id": ref_id(REF_PREFIX, REF_OFFSET, r.referral_id), "hospital": names.get(r.to_hospital, "Unknown"),
            "hospitalId": r.to_hospital, "bedType": r.bed_type, "status": r.status, "time": time_ago(r.created_at),
            "note": r.note or _default_note(r, names.get(r.to_hospital, "")), "priority": r.priority,
            "patientName": p.name if p else "", "fromHospital": names.get(r.from_hospital),
            "ambulanceStatus": r.ambulance_status,
        })
    return out


def _get_referral(db: Session, ident: str) -> Referral:
    pk = parse_ref(ident, REF_PREFIX, REF_OFFSET)
    r = db.get(Referral, pk) if pk is not None else None
    if not r:
        raise HTTPException(404, f"Referral '{ident}' not found")
    return r


def _critical_waiting(db: Session, hospital_id: int, bed_type: str, exclude_referral: int | None = None) -> int:
    ref_q = select(func.count()).select_from(Referral).where(
        Referral.to_hospital == hospital_id, Referral.bed_type == bed_type,
        Referral.status == "Pending", Referral.priority == "Critical")
    if exclude_referral:
        ref_q = ref_q.where(Referral.referral_id != exclude_referral)
    em_q = select(func.count()).select_from(EmergencyRequest).where(
        EmergencyRequest.hospital_id == hospital_id, EmergencyRequest.required_service == bed_type,
        EmergencyRequest.status == "Pending", EmergencyRequest.priority == "Critical")
    return (db.scalar(ref_q) or 0) + (db.scalar(em_q) or 0)


def _free_beds(db: Session, hospital_id: int, bed_type: str) -> int:
    return hs.capacity_for(db, [hospital_id]).get(hospital_id, {}).get(bed_type, {}).get("available", 0)


# ----------------------------------------------------------------------------- bed requests
def create_bed_request(db: Session, user: User, data, lat=None, lng=None) -> dict:
    recommendation = None
    hospital_id = data.hospital_id
    lat = data.latitude if data.latitude is not None else lat
    lng = data.longitude if data.longitude is not None else lng

    if hospital_id is None:  # let the AI choose
        recommendation = ai_service.best_hospital(db, data.bed_type, data.priority, lat, lng)
        if not recommendation:
            raise HTTPException(409, f"No hospital currently has a free {data.bed_type} bed. Try another bed type or call dispatch.")
        hospital_id = recommendation["hospitalId"]
    else:
        hs.get_hospital_or_404(db, hospital_id)
        if _free_beds(db, hospital_id, data.bed_type) == 0:
            alt = ai_service.best_hospital(db, data.bed_type, data.priority, lat, lng)
            hint = f" Suggested alternative: {alt['hospital']} ({alt['available']} free)." if alt else ""
            raise HTTPException(409, f"This hospital has no free {data.bed_type} beds.{hint}")

    patient = get_or_create_patient(db, user, data.patient_name, data.age, data.condition, data.priority)
    ref = Referral(patient_id=patient.patient_id, to_hospital=hospital_id, bed_type=data.bed_type,
                   priority=data.priority, status="Pending", condition=data.condition, note="Waiting for hospital response.")
    db.add(ref)
    db.commit()
    rid = ref_id(REF_PREFIX, REF_OFFSET, ref.referral_id)
    notify.notify_new_request("bed_request", rid, hospital_id, data.priority)
    result = serialize_referrals(db, [ref])[0]
    result["recommendation"] = recommendation
    return result


def list_referrals(db: Session, user: User, limit: int = 100) -> list[dict]:
    q = select(Referral).order_by(Referral.created_at.desc()).limit(limit)
    if user.role == "patient":
        q = q.join(Patient, Patient.patient_id == Referral.patient_id).where(Patient.user_id == user.id)
    elif user.role == "hospital":
        q = q.where((Referral.to_hospital == user.hospital_id) | (Referral.from_hospital == user.hospital_id))
    return serialize_referrals(db, list(db.scalars(q)))


# ----------------------------------------------------------------------------- referral status
def update_referral(db: Session, user: User, ident: str, upd) -> dict:
    r = _get_referral(db, ident)
    if user.role == "hospital" and user.hospital_id not in (r.to_hospital, r.from_hospital):
        raise HTTPException(403, "This referral does not involve your hospital")
    if upd.status is None and upd.ambulance_status is None and upd.note is None:
        raise HTTPException(422, "Provide status, ambulance_status or note")
    patient = db.get(Patient, r.patient_id) if r.patient_id else None
    pname = patient.name if patient else None

    if upd.status and upd.status != r.status:
        if upd.status not in _TRANSITIONS[r.status]:
            raise HTTPException(409, f"Cannot change a {r.status} referral to {upd.status}")
        if upd.status in ("Accepted", "Rejected") and user.role == "ambulance":
            raise HTTPException(403, "Only the receiving hospital can accept or reject a request")

        if upd.status == "Accepted":
            # Critical patients first: don't hand the last beds to a lower-priority patient.
            if r.priority != "Critical" and not upd.force:
                waiting = _critical_waiting(db, r.to_hospital, r.bed_type, exclude_referral=r.referral_id)
                if waiting and _free_beds(db, r.to_hospital, r.bed_type) <= waiting:
                    raise HTTPException(409, f"{waiting} critical patient(s) are waiting for {r.bed_type} beds. "
                                             f"Accept them first (or resend with force=true).")
            bed = bed_service.reserve_bed(db, r.to_hospital, r.bed_type, pname)
            if not bed:
                raise HTTPException(409, f"No free {r.bed_type} bed available to reserve")
            r.bed_id = bed.bed_id
            r.responded_at = utcnow()
        elif upd.status in ("Rejected", "Cancelled"):
            bed_service.release_bed(db, r.bed_id)
            r.bed_id = None
            r.responded_at = r.responded_at or utcnow()
        elif upd.status == "Completed":
            bed_service.occupy_bed(db, r.bed_id, pname)
        r.status = upd.status
        r.note = upd.note or _default_note(r, "")

    if upd.ambulance_status:
        if user.role == "patient":
            raise HTTPException(403, "Not allowed")
        if r.status != "Accepted":
            raise HTTPException(409, "The destination hospital must accept the request before transport can progress")
        cur = AMBULANCE_STEPS.index(r.ambulance_status) if r.ambulance_status in AMBULANCE_STEPS else -1
        new = AMBULANCE_STEPS.index(upd.ambulance_status)
        if new < cur or new > cur + 1:
            nxt = AMBULANCE_STEPS[cur + 1] if cur + 1 < len(AMBULANCE_STEPS) else "(none)"
            raise HTTPException(409, f"Transfer steps must be followed in order. Next step: {nxt}")
        r.ambulance_status = upd.ambulance_status
        amb = db.get(Ambulance, r.ambulance_id) if r.ambulance_id else None
        if amb and upd.ambulance_status == "Handover complete":
            amb.status, amb.destination_hospital_id, amb.eta_minutes = "Available", None, None
        elif amb:
            amb.status = "En route"
        if upd.ambulance_status == "Handover complete":
            bed_service.occupy_bed(db, r.bed_id, pname)
            r.status = "Completed"
            r.note = f"Handover complete. {patient.name if patient else 'Patient'} admitted."
    elif upd.note and not upd.status:
        r.note = upd.note

    db.flush()
    hs.record_snapshot(db, r.to_hospital)
    db.commit()
    notify.notify_status_change("referral", ref_id(REF_PREFIX, REF_OFFSET, r.referral_id), r.status, r.to_hospital)
    notify.notify_capacity_changed(r.to_hospital)
    return serialize_referrals(db, [r])[0]


def _resolve_ambulance(db: Session, ident: str | None) -> Ambulance | None:
    if not ident:
        return None
    amb = db.get(Ambulance, int(ident)) if str(ident).isdigit() else \
        db.scalar(select(Ambulance).where(func.upper(Ambulance.code) == str(ident).upper()))
    if not amb:
        raise HTTPException(404, f"Ambulance '{ident}' not found")
    return amb


def create_transfer(db: Session, user: User, data, lat=None, lng=None) -> dict:
    amb = _resolve_ambulance(db, data.ambulance_id)

    if data.referral_id:  # dispatch an ambulance for an already accepted bed request
        r = _get_referral(db, data.referral_id)
        if r.status != "Accepted":
            raise HTTPException(409, "Only accepted requests can be dispatched for transfer")
        if r.ambulance_status:
            raise HTTPException(409, "An ambulance has already been assigned to this referral")
    else:
        if not data.patient_name:
            raise HTTPException(422, "patient_name is required when referral_id is not given")
        to_id = data.to_hospital_id
        if to_id is None:
            rec = ai_service.best_hospital(db, data.bed_type, data.priority, lat, lng)
            if not rec:
                raise HTTPException(409, f"No hospital has a free {data.bed_type} bed for this transfer")
            to_id = rec["hospitalId"]
        hs.get_hospital_or_404(db, to_id)
        if data.from_hospital_id:
            hs.get_hospital_or_404(db, data.from_hospital_id)
        patient = get_or_create_patient(db, None, data.patient_name, None, data.notes, data.priority)
        bed = bed_service.reserve_bed(db, to_id, data.bed_type, data.patient_name)
        if not bed:
            raise HTTPException(409, f"Destination has no free {data.bed_type} bed")
        r = Referral(patient_id=patient.patient_id, to_hospital=to_id, from_hospital=data.from_hospital_id,
                     bed_id=bed.bed_id, bed_type=data.bed_type, priority=data.priority, status="Accepted",
                     condition=data.notes, responded_at=utcnow())
        db.add(r)
        db.flush()

    r.pickup_location = data.pickup_location or r.pickup_location
    if data.from_hospital_id:
        r.from_hospital = data.from_hospital_id
    r.ambulance_status = AMBULANCE_STEPS[0]
    r.note = f"Transfer in progress. {_names(db, {r.to_hospital}).get(r.to_hospital, 'Destination')} has been notified."
    if amb:
        r.ambulance_id = amb.ambulance_id
        h = db.get(Hospital, r.to_hospital)
        amb.status, amb.destination_hospital_id = "En route", r.to_hospital
        if h and data.pickup_location == "" and r.from_hospital:
            src = db.get(Hospital, r.from_hospital)
            amb.eta_minutes = eta_minutes(hs.haversine_km(src.latitude, src.longitude, h.latitude, h.longitude)) if src else None
    hs.record_snapshot(db, r.to_hospital)
    db.commit()
    rid = ref_id(REF_PREFIX, REF_OFFSET, r.referral_id)
    notify.notify_new_request("transfer", rid, r.to_hospital, r.priority)
    notify.notify_capacity_changed(r.to_hospital)
    return serialize_referrals(db, [r])[0]


# ----------------------------------------------------------------------------- ambulances
def list_ambulances(db: Session) -> list[dict]:
    rows = list(db.scalars(select(Ambulance).order_by(Ambulance.code)))
    names = _names(db, {a.destination_hospital_id for a in rows})
    return [{
        "id": a.code, "crew": a.crew, "status": a.status,
        "destination": names.get(a.destination_hospital_id, "-" if a.status == "Available" else "Unassigned"),
        "eta": f"{a.eta_minutes} min" if a.eta_minutes else "-",
    } for a in rows]


def update_ambulance(db: Session, ident: str, data) -> dict:
    a = _resolve_ambulance(db, ident)
    if data.status:
        if data.status not in ("Available", "En route", "On scene", "Offline"):
            raise HTTPException(422, "status must be Available, En route, On scene or Offline")
        a.status = data.status
    if data.destination_hospital_id is not None:
        hs.get_hospital_or_404(db, data.destination_hospital_id)
        a.destination_hospital_id = data.destination_hospital_id
    if data.eta_minutes is not None:
        a.eta_minutes = data.eta_minutes
    if a.status == "Available":
        a.destination_hospital_id, a.eta_minutes = None, None
    db.commit()
    return next(x for x in list_ambulances(db) if x["id"] == a.code)


# ----------------------------------------------------------------------------- emergencies
def serialize_emergencies(db: Session, rows: list[EmergencyRequest]) -> list[dict]:
    names = _names(db, {e.hospital_id for e in rows})
    patients = _patients(db, {e.patient_id for e in rows})
    out = []
    for e in rows:
        p = patients.get(e.patient_id)
        who = (f"{p.name}, {p.age}" if p and p.age else p.name) if p else "Unknown patient"
        out.append({
            "id": ref_id(EM_PREFIX, EM_OFFSET, e.request_id), "patient": who, "condition": e.condition,
            "priority": e.priority, "bedType": e.required_service,
            "eta": f"{e.eta_minutes} min" if e.eta_minutes else "-", "source": e.source, "status": e.status,
            "hospital": names.get(e.hospital_id), "hospitalId": e.hospital_id, "time": time_ago(e.created_time),
        })
    return out


def _emergency_source(user: User, data) -> str:
    if data.source != "Direct":
        return data.source
    return {"ambulance": "Ambulance", "hospital": "Referral"}.get(user.role, "Direct")


def create_emergency(db: Session, user: User, data, lat=None, lng=None) -> dict:
    lat = data.latitude if data.latitude is not None else lat
    lng = data.longitude if data.longitude is not None else lng
    recommendation, hospital_id, eta = None, data.hospital_id, None

    if hospital_id is not None:
        h = hs.get_hospital_or_404(db, hospital_id)
        eta = eta_minutes(hs.haversine_km(lat if lat is not None else h.latitude, lng if lng is not None else h.longitude,
                                          h.latitude, h.longitude)) if lat is not None else None
    else:
        recommendation = ai_service.best_hospital(db, data.required_service, data.priority, lat, lng)
        if recommendation:
            hospital_id, eta = recommendation["hospitalId"], recommendation["etaMinutes"]

    patient = get_or_create_patient(db, user, data.patient_name, data.age, data.condition, data.priority)
    em = EmergencyRequest(
        patient_id=patient.patient_id, hospital_id=hospital_id, required_service=data.required_service,
        location=data.location, latitude=lat, longitude=lng, condition=data.condition, priority=data.priority,
        status="Pending", source=_emergency_source(user, data), eta_minutes=eta,
    )
    db.add(em)
    db.flush()
    if hospital_id:
        hs.record_snapshot(db, hospital_id)
    db.commit()
    rid = ref_id(EM_PREFIX, EM_OFFSET, em.request_id)
    if hospital_id:
        notify.notify_new_request("emergency", rid, hospital_id, data.priority)
    result = serialize_emergencies(db, [em])[0]
    result["recommendation"] = recommendation
    return result


def list_emergencies(db: Session, user: User, include_closed: bool = False, hospital_id: int | None = None) -> list[dict]:
    q = select(EmergencyRequest)
    if not include_closed:
        q = q.where(EmergencyRequest.status.in_(("Pending", "Accepted")))
    if user.role == "hospital":
        q = q.where(EmergencyRequest.hospital_id == user.hospital_id)
    elif hospital_id:
        q = q.where(EmergencyRequest.hospital_id == hospital_id)
    rows = list(db.scalars(q.limit(300)))
    rows.sort(key=lambda e: (PRIORITY_RANK.get(e.priority, 9), as_utc(e.created_time)))  # Critical first, then oldest
    return serialize_emergencies(db, rows)


def update_emergency(db: Session, user: User, ident: str, status: str) -> dict:
    pk = parse_ref(ident, EM_PREFIX, EM_OFFSET)
    em = db.get(EmergencyRequest, pk) if pk is not None else None
    if not em:
        raise HTTPException(404, f"Emergency request '{ident}' not found")
    if user.role == "hospital" and em.hospital_id != user.hospital_id:
        raise HTTPException(403, "This emergency request is not assigned to your hospital")
    if em.hospital_id is None:
        raise HTTPException(409, "This request has no hospital assigned yet")
    allowed = {"Pending": {"Accepted", "Declined"}, "Accepted": {"Admitted", "Completed", "Declined"},
               "Admitted": {"Completed"}, "Declined": set(), "Completed": set()}
    if status != em.status and status not in allowed[em.status]:
        raise HTTPException(409, f"Cannot change a {em.status} emergency request to {status}")
    p = db.get(Patient, em.patient_id) if em.patient_id else None

    if status == "Accepted" and em.status == "Pending":
        bed = bed_service.reserve_bed(db, em.hospital_id, em.required_service, p.name if p else None)
        if not bed:
            raise HTTPException(409, f"No free {em.required_service} bed to reserve. Decline to reroute the patient.")
        em.bed_id, em.responded_at = bed.bed_id, utcnow()
    elif status == "Declined":
        bed_service.release_bed(db, em.bed_id)
        em.bed_id, em.responded_at = None, em.responded_at or utcnow()
    elif status == "Admitted":
        bed_service.occupy_bed(db, em.bed_id, p.name if p else None)
    elif status == "Completed" and em.bed_id:
        bed = db.get(bed_service.Bed, em.bed_id)
        if bed and bed.status in ("Occupied", "Reserved"):
            bed.status, bed.patient_name = "Cleaning", None
        em.bed_id = None
    em.status = status
    db.flush()
    hs.record_snapshot(db, em.hospital_id)
    db.commit()
    notify.notify_status_change("emergency", ref_id(EM_PREFIX, EM_OFFSET, em.request_id), status, em.hospital_id)
    notify.notify_capacity_changed(em.hospital_id)
    return serialize_emergencies(db, [em])[0]
