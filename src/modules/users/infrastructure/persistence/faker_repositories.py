import asyncio

from faker import Faker
from uuid import UUID

from src.modules.users.domain.entities import UserEntity
from src.modules.users.domain.repositories import UserRepository
from src.shared.infrastructure.persistence.faker_helpers import fake_value

# gencli:faker-repository-imports
from src.modules.users.domain.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.shared.domain.find_by import FindByCriteria, FindByOperator, FindByResult
from src.shared.domain.pagination import CursorPage, KeysetCursor


class FakerUserStore:
    """Almacen en memoria para modo faker, compartido entre peticiones."""

    def __init__(self, seed: int | None = None) -> None:
        self._lock = asyncio.Lock()
        self._items: list[UserEntity] = []
        self._deleted_ids: set[UUID] = set()
        self._faker = Faker()
        if seed is not None:
            Faker.seed(seed)
        seen_emails: set[str] = set()
        for _ in range(25):
            entity = self._make_entity(seen_emails)
            self._items.append(entity)

    def _make_entity(self, seen: set[str] | None = None) -> UserEntity:
        return UserEntity(
            nombre=fake_value("str"),
            email=fake_value("str", seen=seen) if seen else fake_value("str"),
        )

    @property
    def items(self) -> list[UserEntity]:
        return self._items

    @property
    def deleted_ids(self) -> set[UUID]:
        return self._deleted_ids

    @property
    def lock(self) -> asyncio.Lock:
        return self._lock


class FakerUserRepository(UserRepository):
    """Adaptador en memoria del puerto UserRepository para modo faker."""

    def __init__(self, store: FakerUserStore) -> None:
        self._store = store

    def _active(self) -> list[UserEntity]:
        return [
            e for e in self._store.items
            if e.id_user not in self._store.deleted_ids
        ]

    # gencli:faker-repository-methods
    async def soft_delete(self, identifier: UUID) -> None:
        active = self._active()
        if not any(e.id_user == identifier for e in active):
            raise UserNotFoundError("User not found")
        self._store.deleted_ids.add(identifier)

    async def update(self, identifier: UUID, **values: object) -> UserEntity:
        item = None
        for e in self._active():
            if e.id_user == identifier:
                item = e
                break
        if item is None:
            raise UserNotFoundError("User not found")
        if any(
            getattr(e, "email", None) == values["email"]
            for e in self._store.items
            if e.id_user != identifier
        ):
            raise UserAlreadyExistsError("User already exists")
        item.nombre = values["nombre"]  # type: ignore[assignment]
        item.email = values["email"]  # type: ignore[assignment]
        return UserEntity(
                id_user=item.id_user,
                nombre=item.nombre,
                email=item.email,
                created_at=item.created_at
        )

    async def find_by_id(self, identifier: UUID) -> UserEntity | None:
        for item in self._active():
            if item.id_user == identifier:
                return UserEntity(
                id_user=item.id_user,
                nombre=item.nombre,
                email=item.email,
                created_at=item.created_at
                )
        return None

    async def save(self, entity: UserEntity) -> UserEntity:
        if any(
            getattr(e, "email", None) == entity.email
            for e in self._store.items
        ):
            raise UserAlreadyExistsError("User already exists")
        self._store.items.append(entity)
        return entity

    async def find_by(
        self, *, criteria: FindByCriteria, limit: int,
        cursor: KeysetCursor | None, pagination: bool
    ) -> FindByResult[UserEntity]:
        active = sorted(
            self._active(),
            key=lambda e: (e.created_at, e.id_user),
        )

        def _match(e: UserEntity) -> bool:
            val = getattr(e, criteria.field, None)
            if criteria.operator is FindByOperator.EQUALS:
                return val == criteria.value
            if criteria.operator is FindByOperator.CONTAINS:
                return str(criteria.value) in str(val)
            return str(val).startswith(str(criteria.value))

        filtered = [e for e in active if _match(e)]
        if pagination and cursor is not None:
            filtered = [
                e for e in filtered
                if (e.created_at, e.id_user) > (cursor.created_at, cursor.identifier)
            ]
        take = limit + 1 if pagination else limit
        page_rows = filtered[:take]
        has_next = pagination and len(filtered) > take
        next_position = None
        if has_next:
            last = page_rows[-1]
            next_position = KeysetCursor(
                created_at=last.created_at,
                identifier=last.id_user,
            )
        return FindByResult(
            items=[
                UserEntity(
                id_user=item.id_user,
                nombre=item.nombre,
                email=item.email,
                created_at=item.created_at
                )
                for item in page_rows[:limit]
            ],
            next_position=next_position,
            has_next=has_next,
        )

    async def list_paginated(
        self, *, limit: int, cursor: KeysetCursor | None
    ) -> CursorPage[UserEntity]:
        active = sorted(
            self._active(),
            key=lambda e: (e.created_at, e.id_user),
        )
        if cursor is not None:
            active = [
                e for e in active
                if (e.created_at, e.id_user) > (cursor.created_at, cursor.identifier)
            ]
        page_rows = active[:limit]
        has_next = len(active) > limit
        next_position = None
        if has_next:
            last = page_rows[-1]
            next_position = KeysetCursor(
                created_at=last.created_at,
                identifier=last.id_user,
            )
        return CursorPage(
            items=[
                UserEntity(
                id_user=item.id_user,
                nombre=item.nombre,
                email=item.email,
                created_at=item.created_at
                )
                for item in page_rows
            ],
            next_position=next_position,
            has_next=has_next,
        )

    async def list(self, *, limit: int) -> list[UserEntity]:
        active = sorted(
            self._active(),
            key=lambda e: (e.created_at, e.id_user),
        )
        return [
            UserEntity(
            id_user=item.id_user,
            nombre=item.nombre,
            email=item.email,
            created_at=item.created_at
            )
            for item in active[:limit]
        ]