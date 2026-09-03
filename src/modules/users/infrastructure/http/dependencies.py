from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.domain.repositories import UserRepository
from src.modules.users.infrastructure.persistence.repositories import (
    PostgresUserRepository,
)
from src.shared.infrastructure.persistence.database import get_db_session

# gencli:use-case-imports
from src.modules.users.use_cases.delete_users import DeleteUsers
from src.modules.users.use_cases.update_users import UpdateUsers
from src.modules.users.use_cases.get_users import GetUsers
from src.shared.domain.unit_of_work import UnitOfWork
from src.shared.infrastructure.http.dependencies import (
    get_cursor_codec,
    get_unit_of_work,
)
from src.modules.users.use_cases.create_users import CreateUsers
from src.modules.users.use_cases.find_by_users import FindByUsers
from src.shared.domain.pagination import CursorCodec
from src.modules.users.use_cases.list_paginated_users import ListPaginatedUsers
from src.modules.users.use_cases.list_users import ListUsers

def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    """Inyecta el adaptador de persistencia del módulo."""
    return PostgresUserRepository(session)


# gencli:use-case-providers
def get_delete_users(
    repository: UserRepository = Depends(get_user_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> DeleteUsers:
    return DeleteUsers(repository, unit_of_work)
def get_update_users(
    repository: UserRepository = Depends(get_user_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> UpdateUsers:
    return UpdateUsers(repository, unit_of_work)
def get_get_users(
    repository: UserRepository = Depends(get_user_repository),
) -> GetUsers:
    return GetUsers(repository)
def get_create_users(
    repository: UserRepository = Depends(get_user_repository),
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> CreateUsers:
    return CreateUsers(repository, unit_of_work)
def get_find_by_users(
    repository: UserRepository = Depends(get_user_repository),
    cursor_codec: CursorCodec = Depends(get_cursor_codec),
) -> FindByUsers:
    return FindByUsers(repository, cursor_codec)
def get_list_paginated_users(
    repository: UserRepository = Depends(
        get_user_repository
    ),
    cursor_codec: CursorCodec = Depends(get_cursor_codec),
) -> ListPaginatedUsers:
    return ListPaginatedUsers(repository, cursor_codec)
def get_list_users(
    repository: UserRepository = Depends(
        get_user_repository
    ),
) -> ListUsers:
    return ListUsers(repository)
