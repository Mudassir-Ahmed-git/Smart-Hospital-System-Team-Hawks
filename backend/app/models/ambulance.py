from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Ambulance(Base):
    """Needed by the Ambulance dashboard (fleet list with status/destination/ETA)."""
    __tablename__ = "ambulances"

    ambulance_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)  # e.g. A-12
    crew: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(20), default="Available")  # Available | En route | On scene | Offline
    destination_hospital_id: Mapped[int | None] = mapped_column(
        ForeignKey("hospitals.hospital_id", ondelete="SET NULL"), nullable=True
    )
    eta_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
