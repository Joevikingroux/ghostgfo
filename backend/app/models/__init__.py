"""SQLAlchemy ORM models. Importing this package registers every model."""

from app.models.company import Company  # noqa: F401
from app.models.evolution_agent import EvolutionAgent  # noqa: F401
from app.models.report import Report  # noqa: F401
from app.models.upload import Upload  # noqa: F401
from app.models.user import User  # noqa: F401
