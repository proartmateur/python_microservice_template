import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.<snake_name>s.domain.entities import <ent>Entity
from src.modules.<snake_name>s.infrastructure.persistence.models import <ent>Model


class <ent>Repository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_id(self, <snake_name>_id: uuid.UUID) -> Optional[<ent>Entity]:
        stmt = select(<ent>Model).where(<ent>Model.id_<snake_name> == <snake_name>_id)
        result = await self.session.execute(stmt)
        db_<snake_name> = result.scalar_one_or_none()

        if db_<snake_name> is None:
            return None

        return <ent>Entity(
            id_<snake_name>=db_<snake_name>.id_<snake_name>,
(             $camel_prop$=db_<snake_name>.$snake_prop$,
)
            created_at=db_<snake_name>.created_at,
        )

