from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.<snake_name>s.domain.repositories import <ent>Repository

# gencli:repository-adapter-imports

class Postgres<ent>Repository(<ent>Repository):
    """Adaptador PostgreSQL del puerto <ent>Repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # gencli:repository-adapter-methods
