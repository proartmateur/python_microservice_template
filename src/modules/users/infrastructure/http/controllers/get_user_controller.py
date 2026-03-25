import uuid
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.users.infrastructure.persistence.repositories import UserRepository
from src.modules.users.infrastructure.http.schemas import (
    to_user_response,
)
async def get_user_controller(
        user_id: uuid.UUID,
        session: AsyncSession = Depends(get_db_session)
):
    repo = UserRepository(session)
    user = await repo.find_by_id(user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return to_user_response(user)