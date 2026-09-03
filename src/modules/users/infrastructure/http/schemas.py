# gencli:schema-imports
from datetime import datetime
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from src.modules.users.domain.entities import UserEntity
from src.shared.domain.find_by import FindByCriteria, FindByOperator


# gencli:schema-models
class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    nombre: str
    email: str

class UserUpdateResponse(BaseModel):
    id: UUID
    nombre: str
    email: str
    created_at: datetime
class UserGetResponse(BaseModel):
    id: UUID
    nombre: str
    email: str
    created_at: datetime
class UserCreateRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    nombre: str
    email: str

class UserCreateResponse(BaseModel):
    id: UUID
    nombre: str
    email: str
    created_at: datetime
class UserFindByQuery(BaseModel):
    operator: FindByOperator
    value: object

class UserFindByRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    field: str
    query: UserFindByQuery
    pagination: bool = False
    limit: int = 50
    cursor: str | None = None
    _field_types: ClassVar[dict[str, type[object]]] = {
        "nombre": str,
        "email": str
    }

    @model_validator(mode="after")
    def validate_find_by(self) -> "UserFindByRequest":
        expected_type = self._field_types.get(self.field)
        if expected_type is None:
            raise ValueError("field is not searchable")
        if type(self.query.value) is not expected_type:
            raise ValueError("query.value has an invalid type for field")
        is_text_operator = (
            self.query.operator is not FindByOperator.EQUALS
        )
        if is_text_operator and expected_type is not str:
            raise ValueError("operator requires a string field")
        if not 1 <= self.limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        if not self.pagination and self.cursor is not None:
            raise ValueError("cursor requires pagination=true")
        return self

    def to_criteria(self) -> FindByCriteria:
        return FindByCriteria(
            field=self.field, operator=self.query.operator, value=self.query.value
        )

class UserFindByItemResponse(BaseModel):
    id: UUID
    nombre: str
    email: str
    created_at: datetime

class UserFindByResponse(BaseModel):
    items: list[UserFindByItemResponse]
    next_cursor: str | None
    has_next: bool
    limit: int
class UserPaginatedItemResponse(BaseModel):
    id: UUID
    nombre: str
    email: str
    created_at: datetime

class UserPaginatedResponse(BaseModel):
    items: list[UserPaginatedItemResponse]
    next_cursor: str | None
    has_next: bool
    limit: int
class UserResponse(BaseModel):
    id: UUID
    nombre: str
    email: str
    created_at: datetime
# gencli:schema-mappers
def to_user_update_response(entity: UserEntity) -> UserUpdateResponse:
    return UserUpdateResponse(
        id=entity.id_user,
        nombre=entity.nombre,
        email=entity.email,
        created_at=entity.created_at
    )
def to_user_get_response(
    entity: UserEntity,
) -> UserGetResponse:
    return UserGetResponse(
        id=entity.id_user,
        nombre=entity.nombre,
        email=entity.email,
        created_at=entity.created_at
    )
def to_user_create_response(
    entity: UserEntity,
) -> UserCreateResponse:
    return UserCreateResponse(
        id=entity.id_user,
        nombre=entity.nombre,
        email=entity.email,
        created_at=entity.created_at
    )
def to_user_find_by_item_response(
    entity: UserEntity,
) -> UserFindByItemResponse:
    return UserFindByItemResponse(
        id=entity.id_user,
        nombre=entity.nombre,
        email=entity.email,
        created_at=entity.created_at
    )
def to_user_paginated_item_response(
    entity: UserEntity,
) -> UserPaginatedItemResponse:
    return UserPaginatedItemResponse(
        id=entity.id_user,
        nombre=entity.nombre,
        email=entity.email,
        created_at=entity.created_at
    )
def to_user_response(
    entity: UserEntity,
) -> UserResponse:
    return UserResponse(
        id=entity.id_user,
        nombre=entity.nombre,
        email=entity.email,
        created_at=entity.created_at
    )
