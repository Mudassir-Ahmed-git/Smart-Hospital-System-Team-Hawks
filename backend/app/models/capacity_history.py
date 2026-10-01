from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.utils.helpers import utcnow


class CapacityHistory(Base):
    """Time-series snapshots of hospital capacity. Feeds charts and the forecasting model.
    A snapshot is written whenever capacity changes (throttled), plus seeded history."""
    __tablename__ = "capacity_history"
    __table_args__ = (Index("ix_capacity_hospital_date", "hospital_id", "date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hospital_id: Mapped[int] = mapped_column(ForeignKey("hospitals.hospital_id", ondelete="CASCADE"))
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    total_beds: Mapped[int] = mapped_column(Integer, default=0)
    occupied_beds: Mapped[int] = mapped_column(Integer, default=0)
    icu_usage: Mapped[int] = mapped_column(Integer, default=0)  # occupied ICU beds
    emergency_requests: Mapped[int] = mapped_column(Integer, default=0)  # requests in the previous 24h
    # Per-type breakdown so charts/forecasts can be done per ward.
    icu_total: Mapped[int] = mapped_column(Integer, default=0)
    general_total: Mapped[int] = mapped_column(Integer, default=0)
    general_occupied: Mapped[int] = mapped_column(Integer, default=0)
    emergency_total: Mapped[int] = mapped_column(Integer, default=0)
    emergency_occupied: Mapped[int] = mapped_column(Integer, default=0)
