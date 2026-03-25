
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.users.infrastructure.persistence.repositories import UserRepository
from src.modules.users.infrastructure.http.schemas import (
    UserUpdateRequest,
    to_user_response,
)

async def update_user_controller(
        user_id: uuid.UUID,
        payload: UserUpdateRequest,
        session: AsyncSession = Depends(get_db_session)
):
    repo = UserRepository(session)

    try:
        updated_user = await repo.update(
            user_id=user_id,
            nombre=payload.nombre,
            email=payload.email,
        )
    except ValueError as exc:
        message = str(exc)
        if "Ya existe" in message:
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc

    if updated_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return to_user_response(updated_user)