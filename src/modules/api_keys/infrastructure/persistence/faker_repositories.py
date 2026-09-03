import asyncio

from faker import Faker
from uuid import UUID

from datetime import datetime, timezone
from src.modules.api_keys.domain.entities import ApiKeyEntity
from src.modules.api_keys.domain.repositories import ApiKeyRepository


class FakerApiKeyStore:
    """Almacen en memoria para modo faker, compartido entre peticiones."""

    def __init__(self, seed: int | None = None) -> None:
        self._lock = asyncio.Lock()
        self._items: list[ApiKeyEntity] = []
        self._deleted_ids: set[UUID] = set()
        self._faker = Faker()
        if seed is not None:
            Faker.seed(seed)
        self._seed()

    def _seed(self) -> None:
        roles = ("admin", "write", "read")
        for i, role in enumerate(roles):
            entity = ApiKeyEntity(
                name=f"faker-{role}",
                key_prefix=f"pk_{i:08x}",
                key_hash="0" * 64,
                role=role,
                status="active",
            )
            self._items.append(entity)

    @property
    def items(self) -> list[ApiKeyEntity]:
        return self._items

    @property
    def deleted_ids(self) -> set[UUID]:
        return self._deleted_ids

    @property
    def lock(self) -> asyncio.Lock:
        return self._lock


class FakerApiKeyRepository(ApiKeyRepository):
    """Adaptador en memoria del puerto ApiKeyRepository para modo faker."""

    def __init__(self, store: FakerApiKeyStore) -> None:
        self._store = store

    def _active(self) -> list[ApiKeyEntity]:
        return [
            e for e in self._store.items
            if e.id_api_key not in self._store.deleted_ids
        ]

    async def find_by_prefix(self, prefix: str) -> ApiKeyEntity | None:
        for item in self._active():
            if item.key_prefix == prefix:
                return item
        return None

    async def save(self, entity: ApiKeyEntity) -> ApiKeyEntity:
        self._store.items.append(entity)
        return entity

    async def revoke(self, identifier: UUID) -> None:
        for item in self._store.items:
            if item.id_api_key == identifier:
                item.status = "revoked"
                item.revoked_at = datetime.now(timezone.utc)
                self._store.deleted_ids.add(identifier)
                return
        raise ValueError("API key not found")

    async def update_hash(
        self, identifier: UUID, new_hash: str, new_prefix: str
    ) -> None:
        for item in self._store.items:
            if item.id_api_key == identifier:
                item.key_hash = new_hash
                item.key_prefix = new_prefix
                return
        raise ValueError("API key not found")

    async def update_last_used(
        self, identifier: UUID, at: datetime
    ) -> None:
        for item in self._store.items:
            if item.id_api_key == identifier:
                item.last_used_at = at
                return

    async def list(self, *, limit: int) -> list[ApiKeyEntity]:
        return self._active()[:limit]

    async def find_by_id(self, identifier: UUID) -> ApiKeyEntity | None:
        for item in self._active():
            if item.id_api_key == identifier:
                return item
        return None