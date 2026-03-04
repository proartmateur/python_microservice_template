# src/modules/users/infrastructure/http/routers.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.users.infrastructure.persistence.repositories import UserRepository
from src.modules.users.infrastructure.http.schemas import UserResponse, to_user_response

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
        user_id: uuid.UUID,
        session: AsyncSession = Depends(get_db_session)  # Inyeccion de la sesion
):
    # Instanciamos el adaptador (repositorio) pasándole la sesión viva
    repo = UserRepository(session)

    # Delegamos la búsqueda
    user = await repo.find_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return to_user_response(user)
