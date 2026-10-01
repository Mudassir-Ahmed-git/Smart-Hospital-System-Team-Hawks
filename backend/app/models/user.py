from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base
from app.utils.helpers import utcnow


class User(Base):
    """Roles: patient | hospital (Hospital Staff) | ambulance (Ambulance Coordinator) | admin."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), index=True, default="patient")
    # Hospital staff belong to one hospital.
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("hospitals.hospital_id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
