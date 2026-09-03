from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.modules.<snake_name>s.domain.repositories import <ent>Repository
from src.modules.<snake_name>s.infrastructure.persistence.repositories import (
    Postgres<ent>Repository,
)
from src.modules.<snake_name>s.infrastructure.persistence.faker_repositories import (
    Faker<ent>Repository,
    Faker<ent>Store,
)
from src.shared.infrastructure.persistence.database import (
    get_optional_db_session,
)

# gencli:use-case-imports

_faker_<snake_name>_store: Faker<ent>Store | None = None


def get_faker_<snake_name>_store() -> Faker<ent>Store:
    """Provee un store faker singleton por modulo (estado coherente entre requests)."""
    global _faker_<snake_name>_store
    if _faker_<snake_name>_store is None:
        _faker_<snake_name>_store = Faker<ent>Store()
    return _faker_<snake_name>_store


def get_<snake_name>_repository(
    session: AsyncSession | None = Depends(get_optional_db_session),
    store: Faker<ent>Store = Depends(get_faker_<snake_name>_store),
) -> <ent>Repository:
    """Inyecta el adaptador de persistencia del modulo segun el modo configurado."""
    if get_settings().REPOSITORY_DATA_SOURCE == "faker":
        return Faker<ent>Repository(store)
    if session is None:
        raise RuntimeError(
            "La base de datos no ha sido inicializada. Llama a init_db primero."
        )
    return Postgres<ent>Repository(session)


# gencli:use-case-providers