from uuid import UUID

from src.modules.users.infrastructure.http.schemas import (
    UserUpdateRequest,
    UserUpdateResponse,
    to_user_update_response,
)
from src.modules.users.use_cases.update_users import UpdateUsers


async def update_users_controller(
    use_case: UpdateUsers,
    identifier: UUID,
    request: UserUpdateRequest,
) -> UserUpdateResponse:
    entity = await use_case.execute(identifier, **request.model_dump())
    return to_user_update_response(entity)
