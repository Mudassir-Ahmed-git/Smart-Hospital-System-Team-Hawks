from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.patient_schema import BedRequestIn, ReferralOut
from app.services import referral_service as svc
from app.utils.security import get_current_user, require_roles

router = APIRouter(tags=["Patients"])
LAT = Query(None, ge=-90, le=90)
LNG = Query(None, ge=-180, le=180)


@router.post("/patient/request-bed", response_model=ReferralOut, status_code=status.HTTP_201_CREATED,
             summary="Patient requests admission (hospital optional: AI picks one)")
def request_bed(data: BedRequestIn, lat: float | None = LAT, lng: float | None = LNG,
                db: Session = Depends(get_db), user: User = Depends(require_roles("patient"))):
    return svc.create_bed_request(db, user, data, lat, lng)


@router.post("/bed-requests", response_model=ReferralOut, status_code=status.HTTP_201_CREATED,
             summary="Same as /patient/request-bed (path used by the React app)")
def bed_requests(data: BedRequestIn, lat: float | None = LAT, lng: float | None = LNG,
                 db: Session = Depends(get_db), user: User = Depends(require_roles("patient"))):
    return svc.create_bed_request(db, user, data, lat, lng)


@router.get("/patient/status", response_model=list[ReferralOut], summary="Track request status")
def patient_status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.list_referrals(db, user)
