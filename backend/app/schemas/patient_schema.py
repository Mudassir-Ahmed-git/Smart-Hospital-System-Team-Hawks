from pydantic import Field, field_validator

from app.schemas.base import CamelModel
from app.utils.validators import normalize_bed_type, normalize_priority


class BedRequestIn(CamelModel):
    """Body of POST /bed-requests and POST /patient/request-bed (matches the BedRequest page)."""
    hospital_id: int | None = None   # optional: if omitted the AI picks the best hospital
    bed_type: str = "General"
    priority: str = "Normal"
    patient_name: str = Field(min_length=1, max_length=120)
    condition: str = Field(min_length=1, max_length=2000)
    age: int | None = Field(default=None, ge=0, le=130)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("bed_type")
    @classmethod
    def _t(cls, v):
        return normalize_bed_type(v)

    @field_validator("priority")
    @classmethod
    def _p(cls, v):
        return normalize_priority(v)

    @field_validator("hospital_id", mode="before")
    @classmethod
    def _h(cls, v):
        return None if v in ("", None) else v  # the form sends "" when nothing is chosen


class ReferralOut(CamelModel):
    """Shape used by the Referral Status page."""
    id: str
    hospital: str
    hospital_id: int
    bed_type: str
    status: str
    time: str
    note: str
    priority: str = "Normal"
    patient_name: str = ""
    from_hospital: str | None = None
    ambulance_status: str | None = None
    recommendation: dict | None = None  # present on creation when the AI picked the hospital
