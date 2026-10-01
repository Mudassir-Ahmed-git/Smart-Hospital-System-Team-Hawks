from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.patient_schema import ReferralOut
from app.schemas.referral_schema import AmbulanceOut, AmbulanceUpdate, ReferralCreate, ReferralStatusUpdate
from app.services import referral_service as svc
from app.utils.security import get_current_user, require_roles

router = APIRouter(tags=["Referrals & Ambulances"])


@router.post("/referral/create", response_model=ReferralOut, status_code=status.HTTP_201_CREATED,
             summary="Create patient transfer")
def create_referral(data: ReferralCreate, lat: float | None = Query(None, ge=-90, le=90), lng: float | None = Query(None, ge=-180, le=180),
                    db: Session = Depends(get_db), user: User = Depends(require_roles("ambulance", "hospital"))):
    return svc.create_transfer(db, user, data, lat, lng)


@router.put("/referral/{referral_id}/status", response_model=ReferralOut,
            summary="Update transfer status (hospital accepts/rejects; ambulance advances transport steps)")
def update_referral(referral_id: str, data: ReferralStatusUpdate, db: Session = Depends(get_db),
                    user: User = Depends(require_roles("hospital", "ambulance"))):
    return svc.update_referral(db, user, referral_id, data)


@router.get("/referrals", response_model=list[ReferralOut], summary="Referrals visible to the current user")
def list_referrals(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.list_referrals(db, user, limit)


@router.get("/ambulances", response_model=list[AmbulanceOut], summary="Ambulance fleet")
def ambulances(db: Session = Depends(get_db), _: User = Depends(require_roles("ambulance", "hospital"))):
    return svc.list_ambulances(db)


@router.put("/ambulances/{ambulance_id}", response_model=AmbulanceOut, summary="Update ambulance status/destination")
def update_ambulance(ambulance_id: str, data: AmbulanceUpdate, db: Session = Depends(get_db),
                     _: User = Depends(require_roles("ambulance"))):
    return svc.update_ambulance(db, ambulance_id, data)
