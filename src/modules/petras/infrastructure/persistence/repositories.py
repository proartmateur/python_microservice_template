import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.petras.domain.entities import PetraEntity
from src.modules.petras.infrastructure.persistence.models import PetraModel


class PetraRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_id(self, petra_id: uuid.UUID) -> Optional[PetraEntity]:
        stmt = select(PetraModel).where(PetraModel.id_petra == petra_id)
        result = await self.session.execute(stmt)
        db_petra = result.scalar_one_or_none()

        if db_petra is None:
            return None

        return PetraEntity(
            id_petra=db_petra.id_petra,
            name=db_petra.name,
            user=db_petra.user,
            created_at=db_petra.created_at,
        )

