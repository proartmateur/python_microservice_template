import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.users.infrastructure.persistence.models import UserModel
from src.modules.users.domain.entities import UserEntity


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_id(self, user_id: uuid.UUID) -> Optional[UserEntity]:
        """Busca un usuario por su UUID y devuelve la Entidad de Dominio"""

        # 1. Construimos el SELECT
        stmt = select(UserModel).where(UserModel.id_user == user_id)

        # 2. Ejecutamos la consulta asíncrona
        result = await self.session.execute(stmt)

        # 3. Extraemos el objeto de la base de datos
        # scalar_one_or_none() devuelve el registro si existe, o None si no lo encuentra.
        db_user = result.scalar_one_or_none()

        if db_user is None:
            return None

        # 4. Mapeamos el modelo acoplado a la DB hacia tu Entidad pura
        return UserEntity(
            id_user=db_user.id_user,
            nombre=db_user.name,
            email=db_user.email,
            created_at=db_user.created_at,
        )

    async def create(self, nombre: str, email: str) -> UserEntity:
        """Crea un usuario nuevo y devuelve la entidad de dominio persistida."""
        clean_name = nombre.strip()
        clean_email = email.strip()

        if not clean_name:
            raise ValueError("El nombre es obligatorio")
        if "@" not in clean_email:
            raise ValueError("Email inválido")

        user = UserEntity(nombre=clean_name, email=clean_email)
        db_user = UserModel(
            id_user=uuid.UUID(str(user.id_user)),
            name=user.nombre,
            email=user.email,
            created_at=user.created_at,
        )

        self.session.add(db_user)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError("Ya existe un usuario con ese email") from exc

        return user

    async def list_paginated(self, limit: int = 5, page: int = 0) -> list[UserEntity]:
        """Lista usuarios con paginado basado en pagina y limite."""
        if limit is None:
            limit = 5
        if page is None:
            page = 0

        if limit <= 0:
            raise ValueError("limit debe ser mayor a 0")
        if page < 0:
            raise ValueError("page no puede ser negativo")

        offset = page * limit
        stmt = (
            select(UserModel)
            .order_by(UserModel.created_at, UserModel.id_user)
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        db_users = result.scalars().all()

        return [
            UserEntity(
                id_user=db_user.id_user,
                nombre=db_user.name,
                email=db_user.email,
                created_at=db_user.created_at,
            )
            for db_user in db_users
        ]

