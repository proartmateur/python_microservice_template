from src.modules.<snake_name>s.infrastructure.http.schemas import (
    <ent>PaginatedResponse,
    to_<snake_name>_paginated_item_response,
)
from src.modules.<snake_name>s.use_cases.list_paginated_<snake_name>s import ListPaginated<ent>s


async def list_paginated_<snake_name>s_controller(
    use_case: ListPaginated<ent>s,
    *,
    limit: int,
    cursor: str | None,
) -> <ent>PaginatedResponse:
    page = await use_case.execute(limit=limit, cursor=cursor)
    return <ent>PaginatedResponse(
        items=[to_<snake_name>_paginated_item_response(item) for item in page.items],
        next_cursor=page.next_cursor,
        has_next=page.has_next,
        limit=limit,
    )
