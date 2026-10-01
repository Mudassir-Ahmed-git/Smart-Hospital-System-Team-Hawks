from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.hospital_schema import CapacityUpdate, HospitalCreate, HospitalOut
from app.services import hospital_service as svc
from app.utils.security import ensure_hospital_access, get_current_user, require_roles

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


@router.get("", response_model=list[HospitalOut], summary="Get all hospitals (with live bed counts)")
def list_hospitals(
    lat: float | None = Query(None, ge=-90, le=90, description="Caller latitude, for distanceKm"),
    lng: float | None = Query(None, ge=-180, le=180),
    bed_type: str | None = Query(None, description="Only hospitals with a free bed of this type"),
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    hospitals = svc.list_hospitals(db, lat, lng)
    if bed_type:
        from app.utils.validators import normalize_bed_type
        try:
            bt = normalize_bed_type(bed_type)
        except ValueError as e:
            from fastapi import HTTPException
            raise HTTPException(422, str(e))
        hospitals = [h for h in hospitals if h["beds"].get(bt, {}).get("available", 0) > 0]
    return hospitals


@router.get("/{hospital_id}", response_model=HospitalOut, summary="Hospital details")
def get_hospital(hospital_id: int, lat: float | None = Query(None), lng: float | None = Query(None),
                 db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_hospital_dict(db, hospital_id, lat, lng)


@router.post("", response_model=HospitalOut, status_code=status.HTTP_201_CREATED, summary="Register hospital (admin)")
def create_hospital(data: HospitalCreate, db: Session = Depends(get_db), _: User = Depends(require_roles())):
    h = svc.create_hospital(db, data)
    return svc.get_hospital_dict(db, h.hospital_id)


@router.put("/{hospital_id}/capacity", response_model=HospitalOut, summary="Update hospital capacity")
def update_capacity(hospital_id: int, data: CapacityUpdate, db: Session = Depends(get_db),
                    user: User = Depends(require_roles("hospital"))):
    ensure_hospital_access(user, hospital_id)
    hospital = svc.get_hospital_or_404(db, hospital_id)
    svc.set_capacity(db, hospital, data)
    return svc.get_hospital_dict(db, hospital_id)
