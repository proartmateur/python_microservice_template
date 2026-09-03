from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.products.domain.repositories import ProductRepository

# gencli:repository-adapter-imports
from src.modules.products.domain.exceptions import (
    ProductAlreadyExistsError,
    ProductNotFoundError,
)
from typing import cast
from src.shared.domain.find_by import FindByCriteria, FindByOperator, FindByResult
from src.shared.domain.pagination import CursorPage, KeysetCursor
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from src.modules.products.infrastructure.persistence.models import ProductModel
from src.modules.products.domain.entities import ProductEntity

class PostgresProductRepository(ProductRepository):
    """Adaptador PostgreSQL del puerto ProductRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # gencli:repository-adapter-methods
    async def update(self, identifier: UUID, **values: object) -> ProductEntity:
        statement = select(ProductModel).where(
            ProductModel.id_product == identifier,
            ProductModel.deleted_at.is_(None),
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            raise ProductNotFoundError("Product not found")
        model.name = cast('str', values['name'])
        model.price = cast('float', values['price'])
        model.is_physical = cast('bool', values['is_physical'])
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ProductAlreadyExistsError("Product already exists") from exc
        return ProductEntity(
                id_product=model.id_product,
                name=model.name,
                price=model.price,
                is_physical=model.is_physical,
                created_at=model.created_at
        )
    async def find_by(
        self, *, criteria: FindByCriteria, limit: int,
        cursor: KeysetCursor | None, pagination: bool
    ) -> FindByResult[ProductEntity]:
        columns = {
            "name": ProductModel.name,
            "price": ProductModel.price,
            "is_physical": ProductModel.is_physical
        }
        column = columns[criteria.field]
        if criteria.operator is FindByOperator.EQUALS:
            predicate = column == criteria.value
        elif criteria.operator is FindByOperator.CONTAINS:
            predicate = column.contains(criteria.value)
        else:
            predicate = column.startswith(criteria.value)
        statement = select(ProductModel).where(
            ProductModel.deleted_at.is_(None), predicate
        )
        if pagination and cursor is not None:
            statement = statement.where(
                or_(
                    ProductModel.created_at > cursor.created_at,
                    and_(
                        ProductModel.created_at == cursor.created_at,
                        ProductModel.id_product > cursor.identifier,
                    ),
                ),
            )
        statement = statement.order_by(
            ProductModel.created_at, ProductModel.id_product
        ).limit(limit + 1 if pagination else limit)
        result = await self._session.execute(statement)
        rows = list(result.scalars())
        has_next = pagination and len(rows) > limit
        page_rows = rows[:limit]
        next_position = None
        if has_next:
            last_row = page_rows[-1]
            next_position = KeysetCursor(
                created_at=last_row.created_at,
                identifier=last_row.id_product,
            )
        return FindByResult(
            items=[
                ProductEntity(
                id_product=db_product.id_product,
                name=db_product.name,
                price=db_product.price,
                is_physical=db_product.is_physical,
                created_at=db_product.created_at
                )
                for db_product in page_rows
            ],
            next_position=next_position,
            has_next=has_next,
        )
    async def list_paginated(
        self, *, limit: int, cursor: KeysetCursor | None
    ) -> CursorPage[ProductEntity]:
        statement = select(ProductModel).where(
            ProductModel.deleted_at.is_(None)
        )
        if cursor is not None:
            statement = statement.where(
                or_(
                    ProductModel.created_at > cursor.created_at,
                    and_(
                        ProductModel.created_at
                        == cursor.created_at,
                        ProductModel.id_product
                        > cursor.identifier,
                    ),
                ),
            )
        statement = (
            statement.order_by(
                ProductModel.created_at,
                ProductModel.id_product,
            )
            .limit(limit + 1)
        )
        result = await self._session.execute(statement)
        rows = list(result.scalars())
        has_next = len(rows) > limit
        page_rows = rows[:limit]
        next_position = None
        if has_next:
            last_row = page_rows[-1]
            next_position = KeysetCursor(
                created_at=last_row.created_at,
                identifier=last_row.id_product,
            )
        return CursorPage(
            items=[
                ProductEntity(
                id_product=db_product.id_product,
                name=db_product.name,
                price=db_product.price,
                is_physical=db_product.is_physical,
                created_at=db_product.created_at
                )
                for db_product in page_rows
            ],
            next_position=next_position,
            has_next=has_next,
        )
    async def find_by_id(self, identifier: UUID) -> ProductEntity | None:
        statement = select(ProductModel).where(
            ProductModel.id_product == identifier,
            ProductModel.deleted_at.is_(None),
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return ProductEntity(
                id_product=model.id_product,
                name=model.name,
                price=model.price,
                is_physical=model.is_physical,
                created_at=model.created_at
        )
    async def save(self, entity: ProductEntity) -> ProductEntity:
        model = ProductModel(
            id_product=entity.id_product,
            name=entity.name,
            price=entity.price,
            is_physical=entity.is_physical,
            created_at=entity.created_at
        )
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ProductAlreadyExistsError("Product already exists") from exc
        return entity
