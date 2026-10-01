from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.bed_schema import BedCreate, BedOut, BedUpdate
from app.services import bed_service as svc
from app.utils.security import ensure_hospital_access, get_current_user, require_roles
from app.utils.validators import normalize_bed_status, normalize_bed_type

router = APIRouter(prefix="/beds", tags=["Beds"])


def _norm(fn, value):
    if value is None:
        return None
    try:
        return fn(value)
    except ValueError as e:
        raise HTTPException(422, str(e))


def _scope_hospital(user: User, hospital_id: int | None) -> int:
    """Staff are locked to their own hospital; admins must say which one."""
    if user.role == "hospital":
        if hospital_id and hospital_id != user.hospital_id:
            raise HTTPException(403, "You can only manage your own hospital")
        return user.hospital_id
    if hospital_id is None:
        raise HTTPException(422, "hospital_id is required")
    return hospital_id


@router.get("", response_model=list[BedOut], summary="List beds of a hospital (ManageBeds page)")
def list_beds(hospital_id: int | None = None, bed_type: str | None = None, bed_status: str | None = Query(None, alias="status"),
              db: Session = Depends(get_db), user: User = Depends(require_roles("hospital"))):
    hid = _scope_hospital(user, hospital_id)
    return svc.list_beds(db, hid, _norm(normalize_bed_type, bed_type), _norm(normalize_bed_status, bed_status))


@router.get("/available", summary="Find available beds (nearest hospital first)")
def available(bed_type: str | None = None, hospital_id: int | None = None,
              lat: float | None = Query(None, ge=-90, le=90), lng: float | None = Query(None, ge=-180, le=180),
              db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.available_beds(db, _norm(normalize_bed_type, bed_type), hospital_id, lat, lng)


@router.post("", response_model=BedOut, status_code=status.HTTP_201_CREATED, summary="Add bed")
def add_bed(data: BedCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("hospital"))):
    hid = _scope_hospital(user, data.hospital_id)
    bed = svc.create_bed(db, hid, data.bed_type, data.code, data.status)
    return svc.serialize_bed(bed, svc.hospital_name(db, hid))


@router.put("/{bed_ident}", response_model=BedOut, summary="Update bed status (admit / discharge / reserve)")
def update_bed(bed_ident: str, data: BedUpdate, hospital_id: int | None = Query(None, description="Needed only when addressing a bed by code as admin"),
               db: Session = Depends(get_db), user: User = Depends(require_roles("hospital"))):
    hid = user.hospital_id if user.role == "hospital" else hospital_id
    bed = svc.resolve_bed(db, bed_ident, hid)
    ensure_hospital_access(user, bed.hospital_id)
    bed = svc.update_bed_status(db, bed, data.status, data.patient)
    return svc.serialize_bed(bed, svc.hospital_name(db, bed.hospital_id))
