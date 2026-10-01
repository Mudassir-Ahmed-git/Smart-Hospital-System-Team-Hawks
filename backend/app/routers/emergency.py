from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.emergency_schema import EmergencyCreate, EmergencyOut, EmergencyStatusUpdate
from app.services import ai_service
from app.services import referral_service as svc
from app.utils.security import get_current_user, require_roles
from app.utils.validators import normalize_bed_type

router = APIRouter(tags=["Emergency"])


@router.post("/emergency/request", response_model=EmergencyOut, status_code=status.HTTP_201_CREATED,
             summary="Create emergency request (AI assigns the best hospital if none given)")
def create_emergency(data: EmergencyCreate, lat: float | None = Query(None, ge=-90, le=90), lng: float | None = Query(None, ge=-180, le=180),
                     db: Session = Depends(get_db), user: User = Depends(require_roles("patient", "ambulance", "hospital"))):
    return svc.create_emergency(db, user, data, lat, lng)


@router.get("/emergency/nearby-hospitals", summary="Find nearest available hospital (ranked by AI score)")
def nearby_hospitals(bed_type: str = "Emergency", lat: float | None = Query(None, ge=-90, le=90),
                     lng: float | None = Query(None, ge=-180, le=180), priority: str = "Critical",
                     limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    from app.utils.validators import normalize_priority
    try:
        bt, pr = normalize_bed_type(bed_type), normalize_priority(priority)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(422, str(e))
    return ai_service.recommend(db, bt, pr, lat, lng, limit=limit)


@router.get("/emergency-requests", response_model=list[EmergencyOut],
            summary="Active emergency requests, Critical first (Emergency Requests page)")
def list_emergencies(include_closed: bool = False, hospital_id: int | None = None, db: Session = Depends(get_db),
                     user: User = Depends(require_roles("hospital", "ambulance"))):
    return svc.list_emergencies(db, user, include_closed, hospital_id)


@router.put("/emergency/{request_id}/status", response_model=EmergencyOut, summary="Accept / decline / admit / complete")
def update_emergency(request_id: str, data: EmergencyStatusUpdate, db: Session = Depends(get_db),
                     user: User = Depends(require_roles("hospital"))):
    return svc.update_emergency(db, user, request_id, data.status)
