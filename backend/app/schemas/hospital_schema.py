from pydantic import Field, field_validator, model_validator

from app.schemas.base import CamelModel
from app.utils.validators import normalize_bed_type, normalize_emergency_status


class BedCount(CamelModel):
    total: int
    available: int


class HospitalOut(CamelModel):
    id: int
    name: str
    area: str
    address: str
    distance_km: float
    phone: str
    latitude: float
    longitude: float
    x: float            # position on the frontend's schematic map (0-100)
    y: float
    specialties: list[str]
    status: str         # normal | busy | critical (derived from live capacity)
    emergency_status: str  # OPEN | BUSY | CLOSED
    beds: dict[str, BedCount]


class HospitalCreate(CamelModel):
    name: str = Field(min_length=2, max_length=200)
    address: str = ""
    area: str = ""
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    contact_number: str = Field(default="", alias="phone")
    emergency_status: str = "OPEN"
    specialties: list[str] = []
    # Optional initial bed totals, e.g. {"ICU": 10, "General": 50}. Beds are created as Available.
    beds: dict[str, int] = {}

    @field_validator("emergency_status")
    @classmethod
    def _es(cls, v):
        return normalize_emergency_status(v)

    @field_validator("beds")
    @classmethod
    def _beds(cls, v):
        out = {}
        for k, n in v.items():
            if n < 0 or n > 2000:
                raise ValueError("bed totals must be between 0 and 2000")
            out[normalize_bed_type(k)] = n
        return out

    model_config = CamelModel.model_config | {"populate_by_name": True}


class CapacityItem(CamelModel):
    available: int = Field(ge=0)
    total: int | None = Field(default=None, ge=0, le=2000)

    @model_validator(mode="after")
    def _check(self):
        if self.total is not None and self.available > self.total:
            raise ValueError("available cannot exceed total")
        return self


class CapacityUpdate(CamelModel):
    """Body sent by the Update Capacity page: {"beds": {"ICU": {"total": 30, "available": 6}, ...}}"""
    beds: dict[str, CapacityItem]
    emergency_status: str | None = None

    @field_validator("beds")
    @classmethod
    def _beds(cls, v):
        return {normalize_bed_type(k): item for k, item in v.items()}

    @field_validator("emergency_status")
    @classmethod
    def _es(cls, v):
        return normalize_emergency_status(v) if v else None
