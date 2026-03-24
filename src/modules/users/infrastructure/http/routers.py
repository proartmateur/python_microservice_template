import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.infrastructure.http.controllers.update_user_controller import update_user_controller
from src.modules.users.infrastructure.http.controllers.create_user_controller import create_user_controller
from src.modules.users.infrastructure.http.controllers.list_users_controller import list_users_controller
from src.modules.users.infrastructure.http.controllers.get_user_controller import get_user_controller
from src.modules.users.infrastructure.http.controllers.delete_user_controller import delete_user_controller
from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.users.infrastructure.http.schemas import (
    ErrorResponse,
    UserCreateRequest,
    UserPaginatedResponse,
    UserResponse,
    UserUpdateRequest
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    response_model=UserPaginatedResponse,
    summary="Listar usuarios paginados",
    description="Lista usuarios aplicando paginacion por numero de pagina y limite de resultados.",
    response_description="Usuarios paginados",
    responses={
        400: {"model": ErrorResponse, "description": "Parametros de paginacion invalidos"},
        422: {"description": "Error de validacion de FastAPI"},
    },
)
async def list_users(
        limit: int = Query(default=5, ge=1, description="Cantidad maxima de registros por pagina"),
        page: int = Query(default=0, ge=0, description="Indice de pagina (base 0)"),
        session: AsyncSession = Depends(get_db_session)
):
    return await list_users_controller(limit, page, session)


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
    return await create_user_controller(payload, session)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario",
    description="Actualiza un usuario existente por UUID.",
    response_description="Usuario actualizado",
    responses={
        400: {"model": ErrorResponse, "description": "Datos de entrada inválidos"},
        404: {"model": ErrorResponse, "description": "Usuario no encontrado"},
        409: {"model": ErrorResponse, "description": "Email ya existe"},
        422: {"description": "Error de validación de FastAPI"},
    },
)
async def update_user(
        user_id: uuid.UUID,
        payload: UserUpdateRequest,
        session: AsyncSession = Depends(get_db_session)
):
    return await update_user_controller(user_id, payload, session)


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
    return await get_user_controller(user_id, session)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario (soft delete)",
    description="Marca un usuario como eliminado de forma logica sin borrarlo fisicamente de la base de datos.",
    responses={
        204: {"description": "Usuario eliminado logicamente"},
        404: {"model": ErrorResponse, "description": "Usuario no encontrado"},
        422: {"description": "Error de validacion de FastAPI"},
    },
)
async def delete_user(
        user_id: uuid.UUID,
        session: AsyncSession = Depends(get_db_session)
):

    return await delete_user_controller(user_id, session)

