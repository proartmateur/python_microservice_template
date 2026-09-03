from src.modules.users.infrastructure.http.schemas import (
    UserResponse,
    to_user_response,
)
from src.modules.users.use_cases.list_users import ListUsers


async def list_users_controller(
    use_case: ListUsers,
    *,
    limit: int,
) -> list[UserResponse]:
    users = await use_case.execute(limit=limit)
    return [to_user_response(user) for user in users]
