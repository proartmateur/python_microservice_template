from src.modules.products.infrastructure.http.schemas import (
    ProductFindByRequest,
    ProductFindByResponse,
    to_product_find_by_item_response,
)
from src.modules.products.use_cases.find_by_products import FindByProducts


async def find_by_products_controller(
    use_case: FindByProducts,
    request: ProductFindByRequest,
) -> ProductFindByResponse:
    result = await use_case.execute(
        criteria=request.to_criteria(),
        limit=request.limit,
        cursor=request.cursor,
        pagination=request.pagination,
    )
    return ProductFindByResponse(
        items=[to_product_find_by_item_response(item) for item in result.items],
        next_cursor=result.next_cursor,
        has_next=result.has_next,
        limit=request.limit,
    )
