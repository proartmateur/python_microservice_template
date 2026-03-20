from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.modules.users.domain.entities import UserEntity


class UserResponse(BaseModel):
    id: UUID
    nombre: str
    email: str
    created_at: datetime


class UserCreateRequest(BaseModel):
    nombre: str
    email: str


class UserUpdateRequest(BaseModel):
    nombre: str
    email: str


class ErrorResponse(BaseModel):
    detail: str


class UserPaginatedResponse(BaseModel):
    page: int
    total_pages: int
    total_users: int
    limit: int
    has_next: bool
    has_prev: bool
    items: list[UserResponse]


# Explicit mapper keeps HTTP contract decoupled from domain internals.
def to_user_response(user: UserEntity) -> UserResponse:
    return UserResponse(
        id=UUID(str(user.id_user)),
        nombre=user.nombre,
        email=user.email,
        created_at=user.created_at,
    )
