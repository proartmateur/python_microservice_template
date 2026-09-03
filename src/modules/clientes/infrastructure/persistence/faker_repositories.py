import asyncio

from faker import Faker
from uuid import UUID

from src.modules.clientes.domain.entities import ClienteEntity
from src.modules.clientes.domain.repositories import ClienteRepository
from src.shared.infrastructure.persistence.faker_helpers import fake_value

# gencli:faker-repository-imports

class FakerClienteStore:
    """Almacen en memoria para modo faker, compartido entre peticiones."""

    def __init__(self, seed: int | None = None) -> None:
        self._lock = asyncio.Lock()
        self._items: list[ClienteEntity] = []
        self._deleted_ids: set[UUID] = set()
        self._faker = Faker()
        if seed is not None:
            Faker.seed(seed)
        for _ in range(25):
            self._items.append(self._make_entity())

    def _make_entity(self) -> ClienteEntity:
        return ClienteEntity(
           nombre=fake_value("str"),
           email=fake_value("str"),

        )

    @property
    def items(self) -> list[ClienteEntity]:
        return self._items

    @property
    def deleted_ids(self) -> set[UUID]:
        return self._deleted_ids

    @property
    def lock(self) -> asyncio.Lock:
        return self._lock

class FakerClienteRepository(ClienteRepository):
    """Adaptador en memoria del puerto ClienteRepository para modo faker."""

    def __init__(self, store: FakerClienteStore) -> None:
        self._store = store

    def _active(self) -> list[ClienteEntity]:
        return [
            e
            for e in self._store.items
            if e.id_cliente not in self._store.deleted_ids
        ]

    # gencli:faker-repository-methods
    async def find_by_id(self, identifier: UUID) -> ClienteEntity | None:
        for item in self._active():
            if item.id_cliente == identifier:
                return ClienteEntity(
                id_cliente=item.id_cliente,
                nombre=item.nombre,
                email=item.email,
                created_at=item.created_at
                )
        return None
    async def list(self, *, limit: int) -> list[ClienteEntity]:
        active = sorted(
            self._active(),
            key=lambda e: (e.created_at, e.id_cliente),
        )
        return [
            ClienteEntity(
            id_cliente=item.id_cliente,
            nombre=item.nombre,
            email=item.email,
            created_at=item.created_at
            )
            for item in active[:limit]
        ]