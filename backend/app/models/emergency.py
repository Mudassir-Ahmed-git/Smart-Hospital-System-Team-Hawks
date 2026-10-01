from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.utils.helpers import utcnow


class EmergencyRequest(Base):
    __tablename__ = "emergency_requests"
    __table_args__ = (Index("ix_emergency_hospital_status", "hospital_id", "status"),)

    request_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.patient_id", ondelete="SET NULL"), nullable=True)
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("hospitals.hospital_id", ondelete="SET NULL"), nullable=True)
    bed_id: Mapped[int | None] = mapped_column(ForeignKey("beds.bed_id", ondelete="SET NULL"), nullable=True)
    required_service: Mapped[str] = mapped_column(String(20))  # a bed type
    location: Mapped[str] = mapped_column(String(300), default="")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    condition: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(10), default="Urgent")
    status: Mapped[str] = mapped_column(String(12), default="Pending")  # Pending|Accepted|Declined|Admitted|Completed
    source: Mapped[str] = mapped_column(String(60), default="Direct")
    eta_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
