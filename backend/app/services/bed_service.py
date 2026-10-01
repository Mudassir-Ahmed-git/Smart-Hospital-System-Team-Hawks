"""Bed-level operations: add, admit/discharge (status changes), reserve/release."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.bed import Bed
from app.models.hospital import Hospital
from app.services import hospital_service as hs
from app.services import notification_service as notify


def serialize_bed(b: Bed, hospital_name: str) -> dict:
    return {
        "id": b.code, "bedId": b.bed_id, "hospitalId": b.hospital_id, "hospital": hospital_name,
        "ward": b.bed_type, "status": b.status, "patient": b.patient_name or "",
    }


def list_beds(db: Session, hospital_id: int, bed_type: str | None = None, status: str | None = None) -> list[dict]:
    h = hs.get_hospital_or_404(db, hospital_id)
    q = select(Bed).where(Bed.hospital_id == hospital_id).order_by(Bed.bed_type, Bed.code)
    if bed_type:
        q = q.where(Bed.bed_type == bed_type)
    if status:
        q = q.where(Bed.status == status)
    return [serialize_bed(b, h.name) for b in db.scalars(q)]


def available_beds(db: Session, bed_type: str | None, hospital_id: int | None, lat=None, lng=None) -> list[dict]:
    """Hospitals that have free beds, nearest first, with the free beds listed."""
    q = select(Bed).where(Bed.status == "Available")
    if bed_type:
        q = q.where(Bed.bed_type == bed_type)
    if hospital_id:
        q = q.where(Bed.hospital_id == hospital_id)
    by_hospital: dict[int, list[Bed]] = {}
    for b in db.scalars(q.order_by(Bed.bed_type, Bed.code)):
        by_hospital.setdefault(b.hospital_id, []).append(b)
    out = []
    for h in hs.list_hospitals(db, lat, lng):
        beds = by_hospital.get(h["id"])
        if not beds:
            continue
        counts: dict[str, int] = {}
        for b in beds:
            counts[b.bed_type] = counts.get(b.bed_type, 0) + 1
        out.append({
            "hospitalId": h["id"], "hospital": h["name"], "area": h["area"], "distanceKm": h["distanceKm"],
            "emergencyStatus": h["emergencyStatus"], "availableCount": len(beds), "byType": counts,
            "beds": [serialize_bed(b, h["name"]) for b in beds[:50]],
        })
    return sorted(out, key=lambda r: r["distanceKm"])


def resolve_bed(db: Session, ident: str, hospital_id: int | None = None) -> Bed:
    """Accept a numeric bed_id or a bed code like 'ICU-01' (code needs hospital_id to be unambiguous)."""
    bed = None
    if str(ident).isdigit():
        bed = db.get(Bed, int(ident))
    elif hospital_id is not None:
        bed = db.scalar(select(Bed).where(Bed.hospital_id == hospital_id, Bed.code == str(ident).upper()))
    if bed is None:
        raise HTTPException(404, f"Bed '{ident}' not found")
    return bed


def create_bed(db: Session, hospital_id: int, bed_type: str, code: str | None, status: str) -> Bed:
    hs.get_hospital_or_404(db, hospital_id)
    if code:
        code = code.upper()
        if db.scalar(select(Bed.bed_id).where(Bed.hospital_id == hospital_id, Bed.code == code)):
            raise HTTPException(409, f"Bed {code} already exists in this hospital")
        bed = Bed(hospital_id=hospital_id, bed_type=bed_type, code=code, status=status)
        db.add(bed)
    else:
        hs.add_beds(db, hospital_id, bed_type, 1, status)
        bed = db.scalar(select(Bed).where(Bed.hospital_id == hospital_id, Bed.bed_type == bed_type).order_by(Bed.bed_id.desc()))
    db.flush()
    hs.record_snapshot(db, hospital_id)
    db.commit()
    notify.notify_capacity_changed(hospital_id)
    return bed


def update_bed_status(db: Session, bed: Bed, status: str, patient: str | None) -> Bed:
    """Admission (-> Occupied) lowers availability; discharge (-> Available/Cleaning) raises it.
    A bed held for an accepted referral is Reserved; releasing it is done by the referral flow."""
    bed.status = status
    if status in ("Available", "Cleaning"):
        bed.patient_name = None
    elif patient is not None:
        bed.patient_name = patient
    db.flush()
    hs.record_snapshot(db, bed.hospital_id)
    db.commit()
    notify.notify_capacity_changed(bed.hospital_id)
    return bed


def reserve_bed(db: Session, hospital_id: int, bed_type: str, patient_name: str | None = None) -> Bed | None:
    """Atomically pick a free bed and mark it Reserved. Returns None if none are free.
    skip_locked means two staff accepting at once can never grab the same bed (PostgreSQL)."""
    bed = db.scalar(
        select(Bed).where(Bed.hospital_id == hospital_id, Bed.bed_type == bed_type, Bed.status == "Available")
        .order_by(Bed.bed_id).limit(1).with_for_update(skip_locked=True)
    )
    if bed:
        bed.status = "Reserved"
        bed.patient_name = patient_name
        db.flush()
    return bed


def release_bed(db: Session, bed_id: int | None) -> None:
    bed = db.get(Bed, bed_id) if bed_id else None
    if bed and bed.status == "Reserved":
        bed.status, bed.patient_name = "Available", None
        db.flush()


def occupy_bed(db: Session, bed_id: int | None, patient_name: str | None) -> None:
    bed = db.get(Bed, bed_id) if bed_id else None
    if bed:
        bed.status, bed.patient_name = "Occupied", patient_name
        db.flush()


def hospital_name(db: Session, hospital_id: int | None) -> str | None:
    if hospital_id is None:
        return None
    h = db.get(Hospital, hospital_id)
    return h.name if h else None
