from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.domain.repositories import UserRepository

# gencli:repository-adapter-imports
from datetime import datetime, timezone
from src.modules.users.domain.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from typing import cast
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from src.shared.domain.find_by import FindByCriteria, FindByOperator, FindByResult
from src.shared.domain.pagination import CursorPage, KeysetCursor
from src.modules.users.domain.entities import UserEntity
from src.modules.users.infrastructure.persistence.models import UserModel

class PostgresUserRepository(UserRepository):
    """Adaptador PostgreSQL del puerto UserRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # gencli:repository-adapter-methods
    async def soft_delete(self, identifier: UUID) -> None:
        statement = select(UserModel).where(
            UserModel.id_user == identifier,
            UserModel.deleted_at.is_(None),
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            raise UserNotFoundError("User not found")
        model.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
    async def update(self, identifier: UUID, **values: object) -> UserEntity:
        statement = select(UserModel).where(
            UserModel.id_user == identifier,
            UserModel.deleted_at.is_(None),
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            raise UserNotFoundError("User not found")
        model.nombre = cast('str', values['nombre'])
        model.email = cast('str', values['email'])
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise UserAlreadyExistsError("User already exists") from exc
        return UserEntity(
                id_user=model.id_user,
                nombre=model.nombre,
                email=model.email,
                created_at=model.created_at
        )
    async def find_by_id(self, identifier: UUID) -> UserEntity | None:
        statement = select(UserModel).where(
            UserModel.id_user == identifier,
            UserModel.deleted_at.is_(None),
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return UserEntity(
                id_user=model.id_user,
                nombre=model.nombre,
                email=model.email,
                created_at=model.created_at
        )
    async def save(self, entity: UserEntity) -> UserEntity:
        model = UserModel(
            id_user=entity.id_user,
            nombre=entity.nombre,
            email=entity.email,
            created_at=entity.created_at
        )
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise UserAlreadyExistsError("User already exists") from exc
        return entity
    async def find_by(
        self, *, criteria: FindByCriteria, limit: int,
        cursor: KeysetCursor | None, pagination: bool
    ) -> FindByResult[UserEntity]:
        columns = {
            "nombre": UserModel.nombre,
            "email": UserModel.email
        }
        column = columns[criteria.field]
        if criteria.operator is FindByOperator.EQUALS:
            predicate = column == criteria.value
        elif criteria.operator is FindByOperator.CONTAINS:
            predicate = column.contains(criteria.value)
        else:
            predicate = column.startswith(criteria.value)
        statement = select(UserModel).where(
            UserModel.deleted_at.is_(None), predicate
        )
        if pagination and cursor is not None:
            statement = statement.where(
                or_(
                    UserModel.created_at > cursor.created_at,
                    and_(
                        UserModel.created_at == cursor.created_at,
                        UserModel.id_user > cursor.identifier,
                    ),
                )
            )
        statement = statement.order_by(
            UserModel.created_at, UserModel.id_user
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
                identifier=last_row.id_user,
            )
        return FindByResult(
            items=[
                UserEntity(
                id_user=db_user.id_user,
                nombre=db_user.nombre,
                email=db_user.email,
                created_at=db_user.created_at
                )
                for db_user in page_rows
            ],
            next_position=next_position,
            has_next=has_next,
        )
    async def list_paginated(
        self, *, limit: int, cursor: KeysetCursor | None
    ) -> CursorPage[UserEntity]:
        statement = select(UserModel).where(
            UserModel.deleted_at.is_(None)
        )
        if cursor is not None:
            statement = statement.where(
                or_(
                    UserModel.created_at > cursor.created_at,
                    and_(
                        UserModel.created_at
                        == cursor.created_at,
                        UserModel.id_user
                        > cursor.identifier,
                    ),
                )
            )
        statement = (
            statement.order_by(
                UserModel.created_at,
                UserModel.id_user,
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
                identifier=last_row.id_user,
            )
        return CursorPage(
            items=[
                UserEntity(
                id_user=db_user.id_user,
                nombre=db_user.nombre,
                email=db_user.email,
                created_at=db_user.created_at
                )
                for db_user in page_rows
            ],
            next_position=next_position,
            has_next=has_next,
        )
    async def list(self, *, limit: int) -> list[UserEntity]:
        statement = (
            select(UserModel)
            .where(UserModel.deleted_at.is_(None))
            .order_by(
                UserModel.created_at,
                UserModel.id_user,
            )
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return [
            UserEntity(
            id_user=db_user.id_user,
            nombre=db_user.nombre,
            email=db_user.email,
            created_at=db_user.created_at
            )
            for db_user in result.scalars()
        ]
