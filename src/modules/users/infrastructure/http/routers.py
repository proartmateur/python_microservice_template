from typing import Annotated

from fastapi import APIRouter, Depends, Query

# gencli:router-imports
from .controllers.delete_users_controller import delete_users_controller
from src.modules.users.infrastructure.http.dependencies import (
    get_create_users,
    get_delete_users,
    get_find_by_users,
    get_get_users,
    get_list_paginated_users,
    get_list_users,
    get_update_users,
)
from src.modules.users.use_cases.delete_users import DeleteUsers
from .controllers.update_users_controller import update_users_controller
from src.modules.users.infrastructure.http.schemas import (
    UserCreateRequest,
    UserCreateResponse,
    UserFindByRequest,
    UserFindByResponse,
    UserGetResponse,
    UserPaginatedResponse,
    UserResponse,
    UserUpdateRequest,
    UserUpdateResponse,
)
from src.modules.users.use_cases.update_users import UpdateUsers
from uuid import UUID

from .controllers.get_users_controller import get_users_controller
from src.modules.users.use_cases.get_users import GetUsers
from .controllers.create_users_controller import create_users_controller
from src.modules.users.use_cases.create_users import CreateUsers
from .controllers.find_by_users_controller import find_by_users_controller
from src.modules.users.use_cases.find_by_users import FindByUsers
from .controllers.list_paginated_users_controller import list_paginated_users_controller
from src.modules.users.use_cases.list_paginated_users import ListPaginatedUsers
from .controllers.list_users_controller import list_users_controller
from src.modules.users.use_cases.list_users import ListUsers


router = APIRouter(prefix="/users", tags=["Users"])

# gencli:routes
@router.post("/", response_model=UserCreateResponse, status_code=201)
async def create_users(
    request: UserCreateRequest,
    use_case: Annotated[CreateUsers, Depends(get_create_users)],
) -> UserCreateResponse:
    return await create_users_controller(use_case, request)
@router.post("/find-by", response_model=UserFindByResponse)
async def find_by_users(
    request: UserFindByRequest,
    use_case: Annotated[FindByUsers, Depends(get_find_by_users)],
) -> UserFindByResponse:
    return await find_by_users_controller(use_case, request)
@router.get(
    "/paginated",
    response_model=UserPaginatedResponse,
)
async def list_paginated_users(
    use_case: Annotated[
        ListPaginatedUsers,
        Depends(get_list_paginated_users),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
) -> UserPaginatedResponse:
    return await list_paginated_users_controller(
        use_case, limit=limit, cursor=cursor
    )
@router.get("/", response_model=list[UserResponse])
async def list_users(
    use_case: Annotated[
        ListUsers,
        Depends(get_list_users),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[UserResponse]:
    return await list_users_controller(use_case, limit=limit)

@router.get("/{identifier}", response_model=UserGetResponse)
async def get_users(
    identifier: UUID,
    use_case: Annotated[GetUsers, Depends(get_get_users)],
) -> UserGetResponse:
    return await get_users_controller(use_case, identifier)

@router.put("/{identifier}", response_model=UserUpdateResponse)
async def update_users(
    identifier: UUID,
    request: UserUpdateRequest,
    use_case: Annotated[UpdateUsers, Depends(get_update_users)],
) -> UserUpdateResponse:
    return await update_users_controller(use_case, identifier, request)

@router.delete("/{identifier}", status_code=204)
async def delete_users(
    identifier: UUID,
    use_case: Annotated[DeleteUsers, Depends(get_delete_users)],
) -> None:
    await delete_users_controller(use_case, identifier)
