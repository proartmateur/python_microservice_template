from src.modules.users.infrastructure.http.schemas import (
    UserPaginatedResponse,
    to_user_paginated_item_response,
)
from src.modules.users.use_cases.list_paginated_users import ListPaginatedUsers


async def list_paginated_users_controller(
    use_case: ListPaginatedUsers,
    *,
    limit: int,
    cursor: str | None,
) -> UserPaginatedResponse:
    page = await use_case.execute(limit=limit, cursor=cursor)
    return UserPaginatedResponse(
        items=[to_user_paginated_item_response(item) for item in page.items],
        next_cursor=page.next_cursor,
        has_next=page.has_next,
        limit=limit,
    )
