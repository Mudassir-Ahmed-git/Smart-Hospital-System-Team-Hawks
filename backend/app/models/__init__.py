# Import every model so Alembic / metadata.create_all see them.
from app.models.ambulance import Ambulance  # noqa: F401
from app.models.bed import Bed  # noqa: F401
from app.models.capacity_history import CapacityHistory  # noqa: F401
from app.models.emergency import EmergencyRequest  # noqa: F401
from app.models.hospital import Hospital  # noqa: F401
from app.models.patient import Patient  # noqa: F401
from app.models.referral import Referral  # noqa: F401
from app.models.user import User  # noqa: F401
