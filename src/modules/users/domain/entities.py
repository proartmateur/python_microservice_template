from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from uuid6 import uuid7


def get_utc_now() -> datetime:
    """Devuelve la hora actual en UTC para el dominio."""
    return datetime.now(timezone.utc)


@dataclass
class UserEntity:
    nombre: str
    email: str

    id_user: UUID = field(default_factory=uuid7)
    created_at: datetime = field(default_factory=get_utc_now)
