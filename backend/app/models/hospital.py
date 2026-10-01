from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.utils.helpers import utcnow


class Hospital(Base):
    __tablename__ = "hospitals"

    hospital_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    address: Mapped[str] = mapped_column(String(300), default="")
    area: Mapped[str] = mapped_column(String(120), default="")
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    contact_number: Mapped[str] = mapped_column(String(40), default="")
    emergency_status: Mapped[str] = mapped_column(String(10), default="OPEN")  # OPEN | BUSY | CLOSED
    specialties: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    beds = relationship("Bed", back_populates="hospital", cascade="all, delete-orphan")
