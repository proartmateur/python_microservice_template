import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.<snake_name>s.infrastructure.persistence.repositories import <ent>Repository
from src.modules.<snake_name>s.infrastructure.http.schemas import (
    to_<snake_name>_response,
)


async def get_<snake_name>_controller(
        <snake_name>_id: uuid.UUID,
        session: AsyncSession = Depends(get_db_session),
):
    repo = <ent>Repository(session)
    <snake_name> = await repo.find_by_id(<snake_name>_id)

    if <snake_name> is None:
        raise HTTPException(status_code=404, detail="<ent> no encontrado")

    return to_<snake_name>_response(<snake_name>)
