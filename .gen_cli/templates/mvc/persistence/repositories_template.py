import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.<snake_name>s.domain.entities import <ent>Entity
from src.modules.<snake_name>s.infrastructure.persistence.models import <ent>Model


class <ent>Repository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_paginated(self, limit: int = 5, page: int = 0) -> tuple[list[<ent>Entity], int, int]:
        """Lista entidades paginadas y devuelve tambien total de registros y paginas."""
        if limit is None:
            limit = 5
        if page is None:
            page = 0

        if limit <= 0:
            raise ValueError("limit debe ser mayor a 0")
        if page < 0:
            raise ValueError("page no puede ser negativo")

        count_stmt = select(func.count()).select_from(<ent>Model).where(<ent>Model.deleted_at.is_(None))
        count_result = await self.session.execute(count_stmt)
        total_<snake_name>s = count_result.scalar_one()
        total_pages = (total_<snake_name>s + limit - 1) // limit

        offset = page * limit
        stmt = (
            select(<ent>Model)
            .where(<ent>Model.deleted_at.is_(None))
            .order_by(<ent>Model.created_at, <ent>Model.id_<snake_name>)
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        db_<snake_name>s = result.scalars().all()

        <snake_name>s = [
            <ent>Entity(
                id_<snake_name>=db_<snake_name>.id_<snake_name>,
(                $camel_prop$=db_<snake_name>.$snake_prop$,
)
                created_at=db_<snake_name>.created_at,
            )
            for db_<snake_name> in db_<snake_name>s
        ]

        return <snake_name>s, total_<snake_name>s, total_pages

    async def find_by_id(self, <snake_name>_id: uuid.UUID) -> Optional[<ent>Entity]:
        """Busca una entidad por su UUID y devuelve la Entidad de Dominio."""
        stmt = select(<ent>Model).where(
            <ent>Model.id_<snake_name> == <snake_name>_id,
            <ent>Model.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        db_<snake_name> = result.scalar_one_or_none()

        if db_<snake_name> is None:
            return None

        return <ent>Entity(
            id_<snake_name>=db_<snake_name>.id_<snake_name>,
(             $camel_prop$=db_<snake_name>.$snake_prop$,
)
            created_at=db_<snake_name>.created_at,
        )

    async def soft_delete(self, <snake_name>_id: uuid.UUID) -> bool:
        """Marca una entidad como eliminada sin borrarla fisicamente."""
        stmt = select(<ent>Model).where(
            <ent>Model.id_<snake_name> == <snake_name>_id,
            <ent>Model.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        db_<snake_name> = result.scalar_one_or_none()

        if db_<snake_name> is None:
            return False

        db_<snake_name>.deleted_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True

    async def create(
        self,
(        $camel_prop$: $prop_type$,
)
    ) -> <ent>Entity:
        """Crea una entidad nueva y devuelve la entidad de dominio persistida."""
        <snake_name> = <ent>Entity(
(            $camel_prop$=$camel_prop$,
)
        )
        db_<snake_name> = <ent>Model(
            id_<snake_name>=uuid.UUID(str(<snake_name>.id_<snake_name>)),
(            $snake_prop$=<snake_name>.$camel_prop$,
)
            created_at=<snake_name>.created_at,
        )

        self.session.add(db_<snake_name>)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError("Ya existe un <snake_name> con ese valor unico") from exc

        return <snake_name>

    async def update(
        self,
        <snake_name>_id: uuid.UUID,
(        $camel_prop$: $prop_type$,
)
    ) -> Optional[<ent>Entity]:
        """Actualiza una entidad existente por UUID."""
        stmt = select(<ent>Model).where(
            <ent>Model.id_<snake_name> == <snake_name>_id,
            <ent>Model.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        db_<snake_name> = result.scalar_one_or_none()

        if db_<snake_name> is None:
            return None

(         db_<snake_name>.$snake_prop$ = $camel_prop$
)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError("Ya existe un <snake_name> con ese valor unico") from exc

        return <ent>Entity(
            id_<snake_name>=db_<snake_name>.id_<snake_name>,
(            $camel_prop$=db_<snake_name>.$snake_prop$,
)
            created_at=db_<snake_name>.created_at,
        )

