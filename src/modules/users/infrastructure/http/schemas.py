from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.modules.users.domain.entities import UserEntity


class UserResponse(BaseModel):
    id: UUID
    nombre: str
    email: str
    created_at: datetime


# Explicit mapper keeps HTTP contract decoupled from domain internals.
def to_user_response(user: UserEntity) -> UserResponse:
    return UserResponse(
        id=UUID(str(user.id_user)),
        nombre=user.nombre,
        email=user.email,
        created_at=user.created_at,
    )
