from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.shared.domain.pagination import CursorCodec
from src.shared.domain.unit_of_work import UnitOfWork
from src.shared.infrastructure.http.pagination import HmacCursorCodec
from src.shared.infrastructure.persistence.database import get_db_session
from src.shared.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork


def get_unit_of_work(
    session: AsyncSession = Depends(get_db_session),
) -> UnitOfWork:
    """Construye un UoW por petición sobre la sesión inyectada."""
    return SqlAlchemyUnitOfWork(session)


def get_cursor_codec() -> CursorCodec:
    """Construye el verificador de cursores para los endpoints paginados."""
    secret = get_settings().PAGINATION_CURSOR_SECRET
    if secret is None:
        raise RuntimeError(
            "Define PAGINATION_CURSOR_SECRET para usar paginación keyset."
        )
    return HmacCursorCodec(secret)
