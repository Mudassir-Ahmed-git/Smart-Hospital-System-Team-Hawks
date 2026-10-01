from pydantic import Field, field_validator

from app.schemas.base import CamelModel
from app.utils.validators import normalize_bed_type, normalize_priority


class AlertOut(CamelModel):
    type: str          # bed_shortage | icu_overload | emergency_spike
    severity: str      # warning | critical
    hospital_id: int
    hospital: str
    message: str


class DashboardOut(CamelModel):
    total_hospitals: int
    total_beds: int
    available_beds: int
    icu_total: int
    icu_available: int
    icu_occupancy_pct: float
    emergency_requests: int          # currently pending
    emergency_requests_24h: int = Field(alias="emergencyRequests24h")
    pending_referrals: int
    by_type: dict[str, dict]
    alerts: list[AlertOut]


class OccupancyPoint(CamelModel):
    time: str
    # Keys are capitalised on purpose: the frontend chart reads data keys 'ICU', 'General', 'Emergency'.
    ICU: float = Field(alias="ICU")
    General: float = Field(alias="General")
    Emergency: float = Field(alias="Emergency")


class RecommendIn(CamelModel):
    bed_type: str = "ICU"
    priority: str = "Urgent"   # severity
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    specialty: str | None = None
    limit: int = Field(default=3, ge=1, le=10)

    @field_validator("bed_type")
    @classmethod
    def _t(cls, v):
        return normalize_bed_type(v)

    @field_validator("priority")
    @classmethod
    def _p(cls, v):
        return normalize_priority(v)


class ChatIn(CamelModel):
    message: str = Field(min_length=1, max_length=1000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class ChatOut(CamelModel):
    reply: str
    intent: str
    bed_type: str | None = None
    recommendation: dict | None = None
