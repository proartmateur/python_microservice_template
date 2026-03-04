import uuid
from typing import Optional
from sqlalchemy import select
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
        )