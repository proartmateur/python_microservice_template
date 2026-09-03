from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.unit_of_work import UnitOfWork
from src.shared.infrastructure.persistence.database import get_db_session
from src.shared.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork


def get_unit_of_work(
    session: AsyncSession = Depends(get_db_session),
) -> UnitOfWork:
    """Construye un UoW por petición sobre la sesión inyectada."""
    return SqlAlchemyUnitOfWork(session)
