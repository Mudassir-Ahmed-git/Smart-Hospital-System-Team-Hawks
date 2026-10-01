from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.utils.helpers import utcnow


class Referral(Base):
    """A patient bed request / transfer between hospitals.
    - Patient bed request: from_hospital is NULL, status starts Pending.
    - Ambulance transfer: from_hospital (or pickup_location) -> to_hospital, ambulance_status tracks progress."""
    __tablename__ = "referrals"
    __table_args__ = (Index("ix_referral_to_status", "to_hospital", "status"),)

    referral_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.patient_id", ondelete="SET NULL"), nullable=True)
    from_hospital: Mapped[int | None] = mapped_column(ForeignKey("hospitals.hospital_id", ondelete="SET NULL"), nullable=True)
    to_hospital: Mapped[int] = mapped_column(ForeignKey("hospitals.hospital_id", ondelete="CASCADE"))
    ambulance_id: Mapped[int | None] = mapped_column(ForeignKey("ambulances.ambulance_id", ondelete="SET NULL"), nullable=True)
    bed_id: Mapped[int | None] = mapped_column(ForeignKey("beds.bed_id", ondelete="SET NULL"), nullable=True)
    bed_type: Mapped[str] = mapped_column(String(20), default="General")
    priority: Mapped[str] = mapped_column(String(10), default="Normal")
    status: Mapped[str] = mapped_column(String(12), default="Pending")  # Pending|Accepted|Rejected|Completed|Cancelled
    ambulance_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    pickup_location: Mapped[str] = mapped_column(String(300), default="")
    condition: Mapped[str] = mapped_column(Text, default="")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
