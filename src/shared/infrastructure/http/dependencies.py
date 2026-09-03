import secrets

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.shared.domain.pagination import CursorCodec
from src.shared.domain.unit_of_work import UnitOfWork
from src.shared.infrastructure.http.pagination import HmacCursorCodec
from src.shared.infrastructure.persistence.database import (
    get_optional_db_session,
)
from src.shared.infrastructure.persistence.faker_unit_of_work import FakerUnitOfWork
from src.shared.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork


def get_unit_of_work(
    session: AsyncSession | None = Depends(get_optional_db_session),
) -> UnitOfWork:
    """Construye un UoW por petición según el origen de datos configurado."""
    if get_settings().REPOSITORY_DATA_SOURCE == "faker":
        return FakerUnitOfWork()
    if session is None:
        raise RuntimeError(
            "La base de datos no ha sido inicializada. Llama a init_db primero."
        )
    return SqlAlchemyUnitOfWork(session)


def get_cursor_codec() -> CursorCodec:
    """Construye el verificador de cursores para los endpoints paginados."""
    secret = get_settings().PAGINATION_CURSOR_SECRET
    if secret is None:
        # En modo faker se permite un secret efímero por arranque.
        if get_settings().REPOSITORY_DATA_SOURCE == "faker":
            secret = secrets.token_urlsafe(48)
        else:
            raise RuntimeError(
                "Define PAGINATION_CURSOR_SECRET para usar paginación keyset."
            )
    return HmacCursorCodec(secret)