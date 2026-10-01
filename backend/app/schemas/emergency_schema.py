from pydantic import Field, field_validator

from app.schemas.base import CamelModel
from app.utils.validators import EMERGENCY_REQUEST_STATUSES, normalize_bed_type, normalize_priority


class EmergencyCreate(CamelModel):
    patient_name: str = Field(default="Unknown patient", max_length=120)
    age: int | None = Field(default=None, ge=0, le=130)
    condition: str = Field(min_length=1, max_length=2000)
    required_service: str = Field(default="Emergency", alias="bedType")
    priority: str = "Critical"
    location: str = ""
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    hospital_id: int | None = None   # optional override; otherwise AI picks
    source: str = "Direct"

    @field_validator("required_service")
    @classmethod
    def _t(cls, v):
        return normalize_bed_type(v)

    @field_validator("priority")
    @classmethod
    def _p(cls, v):
        return normalize_priority(v)


class EmergencyOut(CamelModel):
    """Shape used by the Emergency Requests page (+ extras)."""
    id: str
    patient: str
    condition: str
    priority: str
    bed_type: str
    eta: str
    source: str
    status: str
    hospital: str | None = None
    hospital_id: int | None = None
    time: str = ""
    recommendation: dict | None = None


class EmergencyStatusUpdate(CamelModel):
    status: str

    @field_validator("status")
    @classmethod
    def _s(cls, v):
        m = {s.lower(): s for s in EMERGENCY_REQUEST_STATUSES}
        m.update({"accept": "Accepted", "decline": "Declined", "rejected": "Declined"})
        if v.strip().lower() not in m:
            raise ValueError(f"Invalid status. Allowed: {', '.join(EMERGENCY_REQUEST_STATUSES)}")
        return m[v.strip().lower()]
