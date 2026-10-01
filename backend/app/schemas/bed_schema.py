from pydantic import Field, field_validator

from app.schemas.base import CamelModel
from app.utils.validators import normalize_bed_status, normalize_bed_type


class BedOut(CamelModel):
    id: str             # bed code, e.g. "ICU-01" (what ManageBeds shows)
    bed_id: int
    hospital_id: int
    hospital: str
    ward: str           # bed type
    status: str
    patient: str = ""


class BedCreate(CamelModel):
    hospital_id: int | None = None   # defaults to the staff member's own hospital
    bed_type: str
    code: str | None = Field(default=None, max_length=20)
    status: str = "Available"

    @field_validator("bed_type")
    @classmethod
    def _t(cls, v):
        return normalize_bed_type(v)

    @field_validator("status")
    @classmethod
    def _s(cls, v):
        return normalize_bed_status(v)


class BedUpdate(CamelModel):
    status: str
    patient: str | None = None  # name of admitted patient; cleared automatically when the bed is freed

    @field_validator("status")
    @classmethod
    def _s(cls, v):
        return normalize_bed_status(v)
