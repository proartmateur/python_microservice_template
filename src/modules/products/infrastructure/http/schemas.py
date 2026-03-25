from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.modules.products.domain.entities import ProductEntity


class ProductResponse(BaseModel):
    id: UUID
    name: str
    user: UUID
    isPhisical: bool

    created_at: datetime


class ProductCreateRequest(BaseModel):
   name: str
   user: UUID
   isPhisical: bool



class ProductUpdateRequest(BaseModel):
   name: str
   user: UUID
   isPhisical: bool



class ErrorResponse(BaseModel):
    detail: str


class ProductPaginatedResponse(BaseModel):
    page: int
    total_pages: int
    total_products: int
    limit: int
    has_next: bool
    has_prev: bool
    items: list[ProductResponse]


# Explicit mapper keeps HTTP contract decoupled from domain internals.
def to_product_response(product: ProductEntity) -> ProductResponse:
    return ProductResponse(
        id=UUID(str(product.id_product)),
       name=product.name,
       user=product.user,
       isPhisical=product.isPhisical,

        created_at=product.created_at,
    )
