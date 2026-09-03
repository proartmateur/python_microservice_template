from uuid import UUID

from src.modules.products.infrastructure.http.schemas import (
    ProductGetResponse,
    to_product_get_response,
)
from src.modules.products.use_cases.get_products import GetProducts


async def get_products_controller(
    use_case: GetProducts,
    identifier: UUID,
) -> ProductGetResponse:
    return to_product_get_response(await use_case.execute(identifier))
