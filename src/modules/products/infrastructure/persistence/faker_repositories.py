import asyncio

from faker import Faker
from uuid import UUID

from src.modules.products.domain.entities import ProductEntity
from src.modules.products.domain.repositories import ProductRepository
from src.shared.infrastructure.persistence.faker_helpers import fake_value

# gencli:faker-repository-imports
from typing import cast
from src.modules.products.domain.exceptions import (
    ProductAlreadyExistsError,
    ProductNotFoundError,
)
from src.shared.domain.find_by import FindByCriteria, FindByOperator, FindByResult
from src.shared.domain.pagination import CursorPage, KeysetCursor

class FakerProductStore:
    """Almacen en memoria para modo faker, compartido entre peticiones."""

    def __init__(self, seed: int | None = None) -> None:
        self._lock = asyncio.Lock()
        self._items: list[ProductEntity] = []
        self._deleted_ids: set[UUID] = set()
        self._faker = Faker()
        if seed is not None:
            Faker.seed(seed)
        for _ in range(25):
            self._items.append(self._make_entity())

    def _make_entity(self) -> ProductEntity:
        return ProductEntity(
           name=fake_value("str"),
           price=fake_value("float"),
           is_physical=fake_value("bool"),

        )

    @property
    def items(self) -> list[ProductEntity]:
        return self._items

    @property
    def deleted_ids(self) -> set[UUID]:
        return self._deleted_ids

    @property
    def lock(self) -> asyncio.Lock:
        return self._lock

class FakerProductRepository(ProductRepository):
    """Adaptador en memoria del puerto ProductRepository para modo faker."""

    def __init__(self, store: FakerProductStore) -> None:
        self._store = store

    def _active(self) -> list[ProductEntity]:
        return [
            e
            for e in self._store.items
            if e.id_product not in self._store.deleted_ids
        ]

    # gencli:faker-repository-methods
    async def update(self, identifier: UUID, **values: object) -> ProductEntity:
        item = None
        for e in self._active():
            if e.id_product == identifier:
                item = e
                break
        if item is None:
            raise ProductNotFoundError("Product not found")
        if any(getattr(e, 'name', None) == values['name']
            for e in self._store.items
            if e.id_product != identifier):
            raise ProductAlreadyExistsError("Product already exists")
        item.name = cast('str', values['name'])
        item.price = cast('float', values['price'])
        item.is_physical = cast('bool', values['is_physical'])
        return ProductEntity(
                id_product=item.id_product,
                name=item.name,
                price=item.price,
                is_physical=item.is_physical,
                created_at=item.created_at
        )
    async def find_by(
        self, *, criteria: FindByCriteria, limit: int,
        cursor: KeysetCursor | None, pagination: bool
    ) -> FindByResult[ProductEntity]:
        active = sorted(
            self._active(),
            key=lambda e: (e.created_at, e.id_product),
        )
        def _match(e: ProductEntity) -> bool:
            val = getattr(e, criteria.field, None)
            if criteria.operator is FindByOperator.EQUALS:
                return val == criteria.value
            if criteria.operator is FindByOperator.CONTAINS:
                return val is not None and criteria.value in val
            return str(val).startswith(str(criteria.value))
        filtered = [e for e in active if _match(e)]
        if pagination and cursor is not None:
            filtered = [
                e for e in filtered
                if (e.created_at, e.id_product) > (cursor.created_at, cursor.identifier)
            ]
        take = limit + 1 if pagination else limit
        page_rows = filtered[:take]
        has_next = pagination and len(filtered) > take
        next_position = None
        if has_next:
            last = page_rows[-1]
            next_position = KeysetCursor(
                created_at=last.created_at,
                identifier=last.id_product,
            )
        return FindByResult(
            items=[
                ProductEntity(
                id_product=item.id_product,
                name=item.name,
                price=item.price,
                is_physical=item.is_physical,
                created_at=item.created_at
                )
                for item in page_rows[:limit]
            ],
            next_position=next_position,
            has_next=has_next,
        )
    async def list_paginated(
        self, *, limit: int, cursor: KeysetCursor | None
    ) -> CursorPage[ProductEntity]:
        active = sorted(
            self._active(),
            key=lambda e: (e.created_at, e.id_product),
        )
        if cursor is not None:
            active = [
                e for e in active
                if (e.created_at, e.id_product) > (cursor.created_at, cursor.identifier)
            ]
        page_rows = active[:limit]
        has_next = len(active) > limit
        next_position = None
        if has_next:
            last = page_rows[-1]
            next_position = KeysetCursor(
                created_at=last.created_at,
                identifier=last.id_product,
            )
        return CursorPage(
            items=[
                ProductEntity(
                id_product=item.id_product,
                name=item.name,
                price=item.price,
                is_physical=item.is_physical,
                created_at=item.created_at
                )
                for item in page_rows
            ],
            next_position=next_position,
            has_next=has_next,
        )
    async def find_by_id(self, identifier: UUID) -> ProductEntity | None:
        for item in self._active():
            if item.id_product == identifier:
                return ProductEntity(
                id_product=item.id_product,
                name=item.name,
                price=item.price,
                is_physical=item.is_physical,
                created_at=item.created_at
                )
        return None
    async def save(self, entity: ProductEntity) -> ProductEntity:
        if any(getattr(e, 'name', None) == entity.name for e in self._store.items):
            raise ProductAlreadyExistsError("Product already exists")
        self._store.items.append(entity)
        return entity