# gencli:schema-imports
from datetime import datetime
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from src.modules.products.domain.entities import ProductEntity
from src.shared.domain.find_by import FindByCriteria, FindByOperator


# gencli:schema-models

class CustomSalesByNameResponse(BaseModel):
    rows: list[dict[str, object]]


class CustomSalesByNameRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str


class CustomInventorySummaryResponse(BaseModel):
    rows: list[dict[str, object]]

class ProductUpdateRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str
    price: float
    is_physical: bool

class ProductUpdateResponse(BaseModel):
    id: UUID
    name: str
    price: float
    is_physical: bool
    created_at: datetime
class ProductFindByQuery(BaseModel):
    operator: FindByOperator
    value: object

class ProductFindByRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    field: str
    query: ProductFindByQuery
    pagination: bool = False
    limit: int = 50
    cursor: str | None = None
    _field_types: ClassVar[dict[str, type[object]]] = {
        "name": str,
        "price": float,
        "is_physical": bool
    }

    @model_validator(mode="after")
    def validate_find_by(self) -> "ProductFindByRequest":
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

class ProductFindByItemResponse(BaseModel):
    id: UUID
    name: str
    price: float
    is_physical: bool
    created_at: datetime

class ProductFindByResponse(BaseModel):
    items: list[ProductFindByItemResponse]
    next_cursor: str | None
    has_next: bool
    limit: int
class ProductPaginatedItemResponse(BaseModel):
    id: UUID
    name: str
    price: float
    is_physical: bool
    created_at: datetime

class ProductPaginatedResponse(BaseModel):
    items: list[ProductPaginatedItemResponse]
    next_cursor: str | None
    has_next: bool
    limit: int
class ProductResponse(BaseModel):
    id: UUID
    name: str
    price: float
    is_physical: bool
    created_at: datetime
class ProductGetResponse(BaseModel):
    id: UUID
    name: str
    price: float
    is_physical: bool
    created_at: datetime
class ProductCreateRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str
    price: float
    is_physical: bool

class ProductCreateResponse(BaseModel):
    id: UUID
    name: str
    price: float
    is_physical: bool
    created_at: datetime
# gencli:schema-mappers
def to_product_update_response(entity: ProductEntity) -> ProductUpdateResponse:
    return ProductUpdateResponse(
        id=entity.id_product,
        name=entity.name,
        price=entity.price,
        is_physical=entity.is_physical,
        created_at=entity.created_at
    )
def to_product_find_by_item_response(
    entity: ProductEntity,
) -> ProductFindByItemResponse:
    return ProductFindByItemResponse(
        id=entity.id_product,
        name=entity.name,
        price=entity.price,
        is_physical=entity.is_physical,
        created_at=entity.created_at
    )
def to_product_paginated_item_response(
    entity: ProductEntity,
) -> ProductPaginatedItemResponse:
    return ProductPaginatedItemResponse(
        id=entity.id_product,
        name=entity.name,
        price=entity.price,
        is_physical=entity.is_physical,
        created_at=entity.created_at
    )
def to_product_response(
    entity: ProductEntity,
) -> ProductResponse:
    return ProductResponse(
        id=entity.id_product,
        name=entity.name,
        price=entity.price,
        is_physical=entity.is_physical,
        created_at=entity.created_at
    )
def to_product_get_response(
    entity: ProductEntity,
) -> ProductGetResponse:
    return ProductGetResponse(
        id=entity.id_product,
        name=entity.name,
        price=entity.price,
        is_physical=entity.is_physical,
        created_at=entity.created_at
    )
def to_product_create_response(
    entity: ProductEntity,
) -> ProductCreateResponse:
    return ProductCreateResponse(
        id=entity.id_product,
        name=entity.name,
        price=entity.price,
        is_physical=entity.is_physical,
        created_at=entity.created_at
    )
