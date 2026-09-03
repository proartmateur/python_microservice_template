import asyncio

from faker import Faker
from uuid import UUID

from src.modules.<snake_name>s.domain.entities import <ent>Entity
from src.modules.<snake_name>s.domain.repositories import <ent>Repository
from src.shared.infrastructure.persistence.faker_helpers import fake_value

# gencli:faker-repository-imports


class Faker<ent>Store:
    """Almacen en memoria para modo faker, compartido entre peticiones."""

    def __init__(self, seed: int | None = None) -> None:
        self._lock = asyncio.Lock()
        self._items: list[<ent>Entity] = []
        self._deleted_ids: set[UUID] = set()
        self._faker = Faker()
        if seed is not None:
            Faker.seed(seed)
        for _ in range(25):
            self._items.append(self._make_entity())

    def _make_entity(self) -> <ent>Entity:
        return <ent>Entity(
(            $snake_prop$=fake_value("$prop_type$"),
)
        )

    @property
    def items(self) -> list[<ent>Entity]:
        return self._items

    @property
    def deleted_ids(self) -> set[UUID]:
        return self._deleted_ids

    @property
    def lock(self) -> asyncio.Lock:
        return self._lock


class Faker<ent>Repository(<ent>Repository):
    """Adaptador en memoria del puerto <ent>Repository para modo faker."""

    def __init__(self, store: Faker<ent>Store) -> None:
        self._store = store

    def _active(self) -> list[<ent>Entity]:
        return [e for e in self._store.items if e.id_<snake_name> not in self._store.deleted_ids]

    # gencli:faker-repository-methods