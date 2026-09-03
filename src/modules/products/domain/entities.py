from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from uuid6 import uuid7


def get_utc_now() -> datetime:
    """Devuelve la hora actual en UTC para el dominio."""
    return datetime.now(timezone.utc)


@dataclass
class ProductEntity:
    name: str
    price: float
    is_physical: bool

    id_product: UUID = field(default_factory=uuid7)
    created_at: datetime = field(default_factory=get_utc_now)
