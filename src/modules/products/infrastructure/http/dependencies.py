from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.modules.products.domain.repositories import ProductRepository
from src.modules.products.infrastructure.persistence.repositories import (
    PostgresProductRepository,
)
from src.modules.products.infrastructure.persistence.faker_repositories import (
    FakerProductRepository,
    FakerProductStore,
)
from src.shared.infrastructure.persistence.database import (
    get_optional_db_session,
)

# gencli:use-case-imports
from src.modules.products.use_cases.update_products import UpdateProducts
from src.modules.products.use_cases.find_by_products import FindByProducts
from src.shared.domain.pagination import CursorCodec
from src.shared.infrastructure.http.dependencies import (
    get_cursor_codec,
    get_unit_of_work,
)
from src.modules.products.use_cases.list_paginated_products import ListPaginatedProducts
from src.modules.products.use_cases.get_products import GetProducts
from src.shared.domain.unit_of_work import UnitOfWork
from src.modules.products.use_cases.create_products import CreateProducts

_faker_product_store: FakerProductStore | None = None

def get_faker_product_store() -> FakerProductStore:
    """Provee un store faker singleton por modulo (estado coherente entre requests)."""
    global _faker_product_store
    if _faker_product_store is None:
        _faker_product_store = FakerProductStore()
    return _faker_product_store

def get_product_repository(
    session: AsyncSession | None = Depends(get_optional_db_session),
    store: FakerProductStore = Depends(get_faker_product_store),
) -> ProductRepository:
    """Inyecta el adaptador de persistencia del modulo segun el modo configurado."""
    if get_settings().REPOSITORY_DATA_SOURCE == "faker":
        return FakerProductRepository(store)
    if session is None:
        raise RuntimeError(
            "La base de datos no ha sido inicializada. Llama a init_db primero."
        )
    return PostgresProductRepository(session)

# gencli:use-case-providers
def get_update_products(
    repository: ProductRepository = Depends(get_product_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> UpdateProducts:
    return UpdateProducts(repository, unit_of_work)
def get_find_by_products(
    repository: ProductRepository = Depends(get_product_repository),
    cursor_codec: CursorCodec = Depends(get_cursor_codec),
) -> FindByProducts:
    return FindByProducts(repository, cursor_codec)
def get_list_paginated_products(
    repository: ProductRepository = Depends(
        get_product_repository
    ),
    cursor_codec: CursorCodec = Depends(get_cursor_codec),
) -> ListPaginatedProducts:
    return ListPaginatedProducts(repository, cursor_codec)
def get_get_products(
    repository: ProductRepository = Depends(get_product_repository),
) -> GetProducts:
    return GetProducts(repository)
def get_create_products(
    repository: ProductRepository = Depends(get_product_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> CreateProducts:
    return CreateProducts(repository, unit_of_work)