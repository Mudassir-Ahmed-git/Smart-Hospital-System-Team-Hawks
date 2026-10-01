from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.capacity_schema import AlertOut, DashboardOut, OccupancyPoint
from app.services import analytics_service as svc
from app.services import hospital_service as hs
from app.utils.security import require_roles

router = APIRouter(tags=["Analytics"])


def _scope(user: User, hospital_id: int | None) -> int | None:
    """Hospital staff only ever see their own hospital; admin/ambulance see the network (or one hospital)."""
    return user.hospital_id if user.role == "hospital" else hospital_id


@router.get("/analytics/dashboard", response_model=DashboardOut, summary="Dashboard KPIs + live alerts")
def dashboard(hospital_id: int | None = None, db: Session = Depends(get_db),
              user: User = Depends(require_roles("hospital", "ambulance"))):
    return svc.dashboard(db, _scope(user, hospital_id))


@router.get("/analytics/capacity", summary="Capacity chart data (per hospital + daily trend)")
def capacity(hospital_id: int | None = None, days: int = Query(7, ge=1, le=60), db: Session = Depends(get_db),
             user: User = Depends(require_roles("hospital", "ambulance"))):
    return svc.capacity_chart(db, _scope(user, hospital_id), days)


@router.get("/analytics/occupancy", response_model=list[OccupancyPoint], summary="Occupancy % by 4-hour slot (last 24h)")
def occupancy(hospital_id: int | None = None, db: Session = Depends(get_db),
              user: User = Depends(require_roles("hospital", "ambulance"))):
    return svc.occupancy_trend(db, _scope(user, hospital_id))


@router.get("/analytics/alerts", response_model=list[AlertOut], summary="Bed shortage / ICU overload / emergency spike alerts")
def alerts(hospital_id: int | None = None, db: Session = Depends(get_db),
           user: User = Depends(require_roles("hospital", "ambulance"))):
    return hs.detect_alerts(db, _scope(user, hospital_id))


@router.get("/reports", summary="Weekly admissions / transfers / wait / peak report (admin)")
def reports(weeks: int = Query(4, ge=1, le=26), db: Session = Depends(get_db), _: User = Depends(require_roles())):
    return svc.weekly_reports(db, weeks)
