from src.modules.products.infrastructure.http.schemas import (
    ProductResponse,
    to_product_response,
)
from src.modules.products.use_cases.list_products import ListProducts


async def list_products_controller(
    use_case: ListProducts,
    *,
    limit: int,
) -> list[ProductResponse]:
    products = await use_case.execute(limit=limit)
    return [to_product_response(product) for product in products]
