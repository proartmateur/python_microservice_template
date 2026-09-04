from typing import Annotated

from fastapi import APIRouter, Depends, Query

# gencli:router-imports
from src.modules.products.use_cases.custom_sales_by_name import CustomSalesByName
from src.modules.products.infrastructure.http.schemas import (
    CustomInventorySummaryResponse,
    CustomSalesByNameRequest,
    CustomSalesByNameResponse,
    ProductCreateRequest,
    ProductCreateResponse,
    ProductFindByRequest,
    ProductFindByResponse,
    ProductGetResponse,
    ProductPaginatedResponse,
    ProductResponse,
    ProductUpdateRequest,
    ProductUpdateResponse,
)
from src.modules.products.infrastructure.http.dependencies import (
    get_create_products,
    get_custom_inventory_summary,
    get_custom_sales_by_name,
    get_delete_products,
    get_find_by_products,
    get_get_products,
    get_list_paginated_products,
    get_list_products,
    get_update_products,
)
from .controllers.custom_sales_by_name_controller import custom_sales_by_name_controller
from src.modules.products.use_cases.custom_inventory_summary import (
    CustomInventorySummary,
)
from .controllers.custom_inventory_summary_controller import (
    custom_inventory_summary_controller,
)
from .controllers.delete_products_controller import delete_products_controller
from src.modules.products.use_cases.delete_products import DeleteProducts
from .controllers.update_products_controller import update_products_controller
from src.modules.products.use_cases.update_products import UpdateProducts
from .controllers.find_by_products_controller import find_by_products_controller
from src.modules.products.use_cases.find_by_products import FindByProducts
from .controllers.list_paginated_products_controller import (
    list_paginated_products_controller,
)
from src.modules.products.use_cases.list_paginated_products import ListPaginatedProducts
from .controllers.list_products_controller import list_products_controller
from src.modules.products.use_cases.list_products import ListProducts
from uuid import UUID

from .controllers.get_products_controller import get_products_controller
from src.modules.products.use_cases.get_products import GetProducts
from .controllers.create_products_controller import create_products_controller
from src.modules.products.use_cases.create_products import CreateProducts


router = APIRouter(prefix="/products", tags=["Products"])

# gencli:routes
@router.post("/find-by", response_model=ProductFindByResponse)
async def find_by_products(
    request: ProductFindByRequest,
    use_case: Annotated[FindByProducts, Depends(get_find_by_products)],
) -> ProductFindByResponse:
    return await find_by_products_controller(use_case, request)
@router.get(
    "/paginated",
    response_model=ProductPaginatedResponse,
)
async def list_paginated_products(
    use_case: Annotated[
        ListPaginatedProducts,
        Depends(get_list_paginated_products),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
) -> ProductPaginatedResponse:
    return await list_paginated_products_controller(
        use_case, limit=limit, cursor=cursor
    )
@router.get("/", response_model=list[ProductResponse])
async def list_products(
    use_case: Annotated[
        ListProducts,
        Depends(get_list_products),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ProductResponse]:
    return await list_products_controller(use_case, limit=limit)
@router.post("/", response_model=ProductCreateResponse, status_code=201)
async def create_products(
    request: ProductCreateRequest,
    use_case: Annotated[CreateProducts, Depends(get_create_products)],
) -> ProductCreateResponse:
    return await create_products_controller(use_case, request)

@router.get("/{identifier}", response_model=ProductGetResponse)
async def get_products(
    identifier: UUID,
    use_case: Annotated[GetProducts, Depends(get_get_products)],
) -> ProductGetResponse:
    return await get_products_controller(use_case, identifier)

@router.put("/{identifier}", response_model=ProductUpdateResponse)
async def update_products(
    identifier: UUID,
    request: ProductUpdateRequest,
    use_case: Annotated[UpdateProducts, Depends(get_update_products)],
) -> ProductUpdateResponse:
    return await update_products_controller(use_case, identifier, request)

@router.delete("/{identifier}", status_code=204)
async def delete_products(
    identifier: UUID,
    use_case: Annotated[DeleteProducts, Depends(get_delete_products)],
) -> None:
    await delete_products_controller(use_case, identifier)

@router.get("/inventory-summary", response_model=CustomInventorySummaryResponse)
async def custom_inventory_summary(
    use_case: Annotated[CustomInventorySummary, Depends(get_custom_inventory_summary)],
) -> CustomInventorySummaryResponse:
    return await custom_inventory_summary_controller(use_case)

@router.post("/sales-by-name", response_model=CustomSalesByNameResponse)
async def custom_sales_by_name(
    request: CustomSalesByNameRequest,
    use_case: Annotated[CustomSalesByName, Depends(get_custom_sales_by_name)],
) -> CustomSalesByNameResponse:
    return await custom_sales_by_name_controller(use_case, request)
