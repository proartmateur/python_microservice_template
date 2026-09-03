from src.modules.products.infrastructure.http.schemas import (
    ProductPaginatedResponse,
    to_product_paginated_item_response,
)
from src.modules.products.use_cases.list_paginated_products import ListPaginatedProducts


async def list_paginated_products_controller(
    use_case: ListPaginatedProducts,
    *,
    limit: int,
    cursor: str | None,
) -> ProductPaginatedResponse:
    page = await use_case.execute(limit=limit, cursor=cursor)
    return ProductPaginatedResponse(
        items=[to_product_paginated_item_response(item) for item in page.items],
        next_cursor=page.next_cursor,
        has_next=page.has_next,
        limit=limit,
    )
