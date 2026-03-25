import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.products.domain.entities import ProductEntity
from src.modules.products.infrastructure.persistence.models import ProductModel


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_paginated(self, limit: int = 5, page: int = 0) -> tuple[list[ProductEntity], int, int]:
        """Lista entidades paginadas y devuelve tambien total de registros y paginas."""
        if limit is None:
            limit = 5
        if page is None:
            page = 0

        if limit <= 0:
            raise ValueError("limit debe ser mayor a 0")
        if page < 0:
            raise ValueError("page no puede ser negativo")

        count_stmt = select(func.count()).select_from(ProductModel).where(ProductModel.deleted_at.is_(None))
        count_result = await self.session.execute(count_stmt)
        total_products = count_result.scalar_one()
        total_pages = (total_products + limit - 1) // limit

        offset = page * limit
        stmt = (
            select(ProductModel)
            .where(ProductModel.deleted_at.is_(None))
            .order_by(ProductModel.created_at, ProductModel.id_product)
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        db_products = result.scalars().all()

        products = [
            ProductEntity(
                id_product=db_product.id_product,
                name=db_product.name,
                user=db_product.user,
                isPhisical=db_product.is_phisical,

                created_at=db_product.created_at,
            )
            for db_product in db_products
        ]

        return products, total_products, total_pages

    async def find_by_id(self, product_id: uuid.UUID) -> Optional[ProductEntity]:
        """Busca una entidad por su UUID y devuelve la Entidad de Dominio."""
        stmt = select(ProductModel).where(
            ProductModel.id_product == product_id,
            ProductModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        db_product = result.scalar_one_or_none()

        if db_product is None:
            return None

        return ProductEntity(
            id_product=db_product.id_product,
            name=db_product.name,
            user=db_product.user,
            isPhisical=db_product.is_phisical,

            created_at=db_product.created_at,
        )

    async def soft_delete(self, product_id: uuid.UUID) -> bool:
        """Marca una entidad como eliminada sin borrarla fisicamente."""
        stmt = select(ProductModel).where(
            ProductModel.id_product == product_id,
            ProductModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        db_product = result.scalar_one_or_none()

        if db_product is None:
            return False

        db_product.deleted_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True

    async def create(
        self,
       name: str,
       user: uuid.UUID,
       isPhisical: bool,

    ) -> ProductEntity:
        """Crea una entidad nueva y devuelve la entidad de dominio persistida."""
        product = ProductEntity(
           name=name,
           user=user,
           isPhisical=isPhisical,

        )
        db_product = ProductModel(
            id_product=uuid.UUID(str(product.id_product)),
           name=product.name,
           user=product.user,
           is_phisical=product.isPhisical,

            created_at=product.created_at,
        )

        self.session.add(db_product)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError("Ya existe un product con ese valor unico") from exc

        return product

    async def update(
        self,
        product_id: uuid.UUID,
       name: str,
       user: uuid.UUID,
       isPhisical: bool,

    ) -> Optional[ProductEntity]:
        """Actualiza una entidad existente por UUID."""
        stmt = select(ProductModel).where(
            ProductModel.id_product == product_id,
            ProductModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        db_product = result.scalar_one_or_none()

        if db_product is None:
            return None

        db_product.name = name
        db_product.user = user
        db_product.is_phisical = isPhisical


        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError("Ya existe un product con ese valor unico") from exc

        return ProductEntity(
            id_product=db_product.id_product,
           name=db_product.name,
           user=db_product.user,
           isPhisical=db_product.is_phisical,

            created_at=db_product.created_at,
        )

