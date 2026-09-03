from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.<snake_name>s.domain.repositories import <ent>Repository
from src.modules.<snake_name>s.infrastructure.persistence.repositories import (
    Postgres<ent>Repository,
)
from src.shared.infrastructure.persistence.database import get_db_session

# gencli:use-case-imports

def get_<snake_name>_repository(
    session: AsyncSession = Depends(get_db_session),
) -> <ent>Repository:
    """Inyecta el adaptador de persistencia del módulo."""
    return Postgres<ent>Repository(session)


# gencli:use-case-providers
