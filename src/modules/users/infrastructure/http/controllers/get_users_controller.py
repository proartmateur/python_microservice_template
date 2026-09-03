from uuid import UUID

from src.modules.users.infrastructure.http.schemas import (
    UserGetResponse,
    to_user_get_response,
)
from src.modules.users.use_cases.get_users import GetUsers


async def get_users_controller(
    use_case: GetUsers,
    identifier: UUID,
) -> UserGetResponse:
    return to_user_get_response(await use_case.execute(identifier))
