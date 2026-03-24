
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.users.infrastructure.persistence.repositories import UserRepository
from src.modules.users.infrastructure.http.schemas import (
    UserCreateRequest,
    to_user_response,
)

async def create_user_controller(
        payload: UserCreateRequest,
        session: AsyncSession = Depends(get_db_session)  # Inyeccion de la sesion
):
    repo = UserRepository(session)

    try:
        user = await repo.create(nombre=payload.nombre, email=payload.email)
    except ValueError as exc:
        message = str(exc)
        if "Ya existe" in message:
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc

    return to_user_response(user)