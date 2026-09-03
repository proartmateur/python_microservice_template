from uuid import UUID

from src.modules.products.infrastructure.http.schemas import (
    ProductUpdateRequest,
    ProductUpdateResponse,
    to_product_update_response,
)
from src.modules.products.use_cases.update_products import UpdateProducts


async def update_products_controller(
    use_case: UpdateProducts,
    identifier: UUID,
    request: ProductUpdateRequest,
) -> ProductUpdateResponse:
    entity = await use_case.execute(identifier, **request.model_dump())
    return to_product_update_response(entity)
