from src.modules.products.infrastructure.http.schemas import (
    ProductCreateRequest,
    ProductCreateResponse,
    to_product_create_response,
)
from src.modules.products.use_cases.create_products import CreateProducts


async def create_products_controller(
    use_case: CreateProducts,
    request: ProductCreateRequest,
) -> ProductCreateResponse:
    entity = await use_case.execute(**request.model_dump())
    return to_product_create_response(entity)
