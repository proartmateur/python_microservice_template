import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.users.infrastructure.persistence.repositories import UserRepository


async def delete_user_controller(
        user_id: uuid.UUID,
        session: AsyncSession = Depends(get_db_session)
):
    repo = UserRepository(session)
    was_deleted = await repo.soft_delete(user_id)

    if not was_deleted:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
