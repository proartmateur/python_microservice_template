# src/modules/users/infrastructure/http/routers.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.users.infrastructure.persistence.repositories import UserRepository
from src.modules.users.infrastructure.http.schemas import (
    ErrorResponse,
    UserCreateRequest,
    UserResponse,
    to_user_response,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    description="Crea un nuevo usuario y lo persiste en la base de datos.",
    response_description="Usuario creado",
    responses={
        400: {"model": ErrorResponse, "description": "Datos de entrada inválidos"},
        409: {"model": ErrorResponse, "description": "Email ya existe"},
        422: {"description": "Error de validación de FastAPI"},
    },
)
async def create_user(
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


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Obtener usuario por ID",
    description="Recupera un usuario por UUID desde la capa de persistencia.",
    response_description="Usuario encontrado",
    responses={404: {"description": "Usuario no encontrado"}},
)
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
