from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.utils.helpers import utcnow


class Bed(Base):
    """One physical bed. Capacity numbers are always derived by counting rows,
    so 'available' can never drift from reality."""
    __tablename__ = "beds"
    __table_args__ = (
        UniqueConstraint("hospital_id", "code", name="uq_bed_hospital_code"),
        Index("ix_bed_lookup", "hospital_id", "bed_type", "status"),
    )

    bed_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.hospital_id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(20))  # e.g. ICU-01 (what the UI shows)
    bed_type: Mapped[str] = mapped_column(String(20))  # ICU | General | Emergency | Ventilator | Operation Theater
    status: Mapped[str] = mapped_column(String(12), default="Available")  # Available | Occupied | Reserved | Cleaning
    patient_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    hospital = relationship("Hospital", back_populates="beds")
