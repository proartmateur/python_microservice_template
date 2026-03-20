# src/modules/users/infrastructure/http/routers.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.users.infrastructure.persistence.repositories import UserRepository
from src.modules.users.infrastructure.http.schemas import (
    ErrorResponse,
    UserCreateRequest,
    UserPaginatedResponse,
    UserResponse,
    to_user_response,
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
    repo = UserRepository(session)

    try:
        users, total_users, total_pages = await repo.list_paginated(limit=limit, page=page)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    has_prev = page > 0
    has_next = (page + 1) < total_pages

    return UserPaginatedResponse(
        page=page,
        total_pages=total_pages,
        total_users=total_users,
        limit=limit,
        has_next=has_next,
        has_prev=has_prev,
        items=[to_user_response(user) for user in users],
    )


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
    repo = UserRepository(session)
    was_deleted = await repo.soft_delete(user_id)

    if not was_deleted:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return Response(status_code=status.HTTP_204_NO_CONTENT)

