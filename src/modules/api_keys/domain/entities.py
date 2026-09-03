from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from uuid6 import uuid7


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ApiKeyEntity:
    name: str
    key_prefix: str
    key_hash: str
    role: str
    status: str

    id_api_key: UUID = field(default_factory=uuid7)
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None
    created_at: datetime = field(default_factory=get_utc_now)