from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.capacity_schema import ChatIn, ChatOut, RecommendIn
from app.services import ai_service
from app.utils.security import get_current_user

router = APIRouter(tags=["AI"])


@router.post("/ai/recommend", summary="Hospital recommendation (availability 40%, distance 30%, capability 20%, wait 10%)")
def recommend(data: RecommendIn, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    recs = ai_service.recommend(db, data.bed_type, data.priority, data.latitude, data.longitude, data.specialty, data.limit)
    if not recs:
        return {"recommended": None, "alternatives": [],
                "message": f"No hospital currently has a free {data.bed_type} bed."}
    top = recs[0]
    return {"recommended": top, "alternatives": recs[1:],
            "message": f"Recommended hospital: {top['hospital']}. Reason: {top['reason']}."}


@router.get("/ai/predict", summary="Capacity forecast, e.g. 'ICU demand may increase 20% tomorrow'")
def predict(hospital_id: int | None = Query(None, description="Omit for network-wide"),
            bed_type: str = Query("ICU", description="ICU | General | Emergency | Overall"),
            db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if bed_type != "Overall":
        from app.utils.validators import normalize_bed_type
        try:
            bed_type = normalize_bed_type(bed_type)
        except ValueError as e:
            raise HTTPException(422, str(e))
        if bed_type not in ("ICU", "General", "Emergency"):
            raise HTTPException(422, "Forecasts are available for ICU, General, Emergency or Overall")
    return ai_service.predict(db, hospital_id, bed_type)


@router.post("/ai/chat", response_model=ChatOut, summary="AI healthcare assistant")
def chat(data: ChatIn, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return ai_service.chat(db, data.message, data.latitude, data.longitude)


@router.post("/assistant", response_model=ChatOut, summary="Alias of /ai/chat (path used by the React chat box)")
def assistant(data: ChatIn, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return ai_service.chat(db, data.message, data.latitude, data.longitude)
