from src.modules.users.infrastructure.http.schemas import (
    UserCreateRequest,
    UserCreateResponse,
    to_user_create_response,
)
from src.modules.users.use_cases.create_users import CreateUsers


async def create_users_controller(
    use_case: CreateUsers,
    request: UserCreateRequest,
) -> UserCreateResponse:
    entity = await use_case.execute(**request.model_dump())
    return to_user_create_response(entity)
