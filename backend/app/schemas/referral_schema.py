from pydantic import Field, field_validator

from app.schemas.base import CamelModel
from app.utils.validators import AMBULANCE_STEPS, REFERRAL_STATUSES, normalize_bed_type, normalize_priority


class ReferralCreate(CamelModel):
    """Creates an ambulance transfer. Either link an existing accepted bed request (referral_id)
    or describe a new transfer."""
    referral_id: str | None = None
    patient_name: str | None = Field(default=None, max_length=120)
    from_hospital_id: int | None = None
    pickup_location: str = ""
    to_hospital_id: int | None = None
    bed_type: str = "General"
    priority: str = "Urgent"
    notes: str = ""
    ambulance_id: str | None = None   # code (A-12) or numeric id

    @field_validator("bed_type")
    @classmethod
    def _t(cls, v):
        return normalize_bed_type(v)

    @field_validator("priority")
    @classmethod
    def _p(cls, v):
        return normalize_priority(v)


class ReferralStatusUpdate(CamelModel):
    status: str | None = None             # Pending|Accepted|Rejected|Completed|Cancelled
    ambulance_status: str | None = None   # one of AMBULANCE_STEPS
    note: str | None = Field(default=None, max_length=1000)
    force: bool = False                   # accept a non-critical request even if critical patients are waiting

    @field_validator("status")
    @classmethod
    def _s(cls, v):
        if v is None:
            return v
        m = {s.lower(): s for s in REFERRAL_STATUSES}
        m.update({"declined": "Rejected", "accept": "Accepted", "reject": "Rejected"})
        if v.strip().lower() not in m:
            raise ValueError(f"Invalid status. Allowed: {', '.join(REFERRAL_STATUSES)}")
        return m[v.strip().lower()]

    @field_validator("ambulance_status")
    @classmethod
    def _a(cls, v):
        if v is None:
            return v
        m = {s.lower(): s for s in AMBULANCE_STEPS}
        if v.strip().lower() not in m:
            raise ValueError(f"Invalid ambulance_status. Allowed: {', '.join(AMBULANCE_STEPS)}")
        return m[v.strip().lower()]


class AmbulanceOut(CamelModel):
    id: str
    crew: str
    status: str
    destination: str
    eta: str


class AmbulanceUpdate(CamelModel):
    status: str | None = None
    destination_hospital_id: int | None = None
    eta_minutes: int | None = Field(default=None, ge=0)
