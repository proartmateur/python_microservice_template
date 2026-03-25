import uuid

from fastapi import Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.<snake_name>s.infrastructure.persistence.repositories import <ent>Repository


async def delete_<snake_name>_controller(
        <snake_name>_id: uuid.UUID,
        session: AsyncSession = Depends(get_db_session),
):
    repo = <ent>Repository(session)
    was_deleted = await repo.soft_delete(<snake_name>_id)

    if not was_deleted:
        raise HTTPException(status_code=404, detail="<ent> no encontrado")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
