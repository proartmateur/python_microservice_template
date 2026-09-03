from src.modules.users.infrastructure.http.schemas import (
    UserFindByRequest,
    UserFindByResponse,
    to_user_find_by_item_response,
)
from src.modules.users.use_cases.find_by_users import FindByUsers


async def find_by_users_controller(
    use_case: FindByUsers,
    request: UserFindByRequest,
) -> UserFindByResponse:
    result = await use_case.execute(
        criteria=request.to_criteria(),
        limit=request.limit,
        cursor=request.cursor,
        pagination=request.pagination,
    )
    return UserFindByResponse(
        items=[to_user_find_by_item_response(item) for item in result.items],
        next_cursor=result.next_cursor,
        has_next=result.has_next,
        limit=request.limit,
    )
