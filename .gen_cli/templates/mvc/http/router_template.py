import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.<snake_name>s.infrastructure.http.controllers.create_<snake_name>_controller import create_<snake_name>_controller
from src.modules.<snake_name>s.infrastructure.http.controllers.get_<snake_name>_controller import get_<snake_name>_controller
from src.modules.<snake_name>s.infrastructure.http.controllers.list_<snake_name>s_controller import list_<snake_name>s_controller
from src.modules.<snake_name>s.infrastructure.http.controllers.update_<snake_name>_controller import update_<snake_name>_controller
from src.modules.<snake_name>s.infrastructure.http.controllers.delete_<snake_name>_controller import delete_<snake_name>_controller
from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.<snake_name>s.infrastructure.http.schemas import (
    ErrorResponse,
    <ent>CreateRequest,
    <ent>PaginatedResponse,
    <ent>Response,
    <ent>UpdateRequest,
)

router = APIRouter(prefix="/<kebab_name>s", tags=["<ent>s"])


@router.get(
    "/",
    response_model=<ent>PaginatedResponse,
    summary="Listar <snake_name>s paginados",
    description="Lista <snake_name>s aplicando paginacion por numero de pagina y limite de resultados.",
    response_description="<ent>s paginados",
    responses={
        400: {"model": ErrorResponse, "description": "Parametros de paginacion invalidos"},
        422: {"description": "Error de validacion de FastAPI"},
    },
)
async def list_<snake_name>s(
        limit: int = Query(default=5, ge=1, description="Cantidad maxima de registros por pagina"),
        page: int = Query(default=0, ge=0, description="Indice de pagina (base 0)"),
        session: AsyncSession = Depends(get_db_session),
):
    return await list_<snake_name>s_controller(limit, page, session)


@router.post(
    "/",
    response_model=<ent>Response,
    status_code=status.HTTP_201_CREATED,
    summary="Crear <snake_name>",
    description="Crea un nuevo <snake_name> y lo persiste en la base de datos.",
    response_description="<ent> creado",
    responses={
        400: {"model": ErrorResponse, "description": "Datos de entrada inválidos"},
        409: {"model": ErrorResponse, "description": "Conflicto por restricción única"},
        422: {"description": "Error de validación de FastAPI"},
    },
)
async def create_<snake_name>(
        payload: <ent>CreateRequest,
        session: AsyncSession = Depends(get_db_session),
):
    return await create_<snake_name>_controller(payload, session)


@router.put(
    "/{<snake_name>_id}",
    response_model=<ent>Response,
    summary="Actualizar <snake_name>",
    description="Actualiza un <snake_name> existente por UUID.",
    response_description="<ent> actualizado",
    responses={
        400: {"model": ErrorResponse, "description": "Datos de entrada inválidos"},
        404: {"model": ErrorResponse, "description": "<ent> no encontrado"},
        409: {"model": ErrorResponse, "description": "Conflicto por restricción única"},
        422: {"description": "Error de validación de FastAPI"},
    },
)
async def update_<snake_name>(
        <snake_name>_id: uuid.UUID,
        payload: <ent>UpdateRequest,
        session: AsyncSession = Depends(get_db_session),
):
    return await update_<snake_name>_controller(<snake_name>_id, payload, session)


@router.get(
    "/{<snake_name>_id}",
    response_model=<ent>Response,
    summary="Obtener <snake_name> por ID",
    description="Recupera un <snake_name> por UUID desde la capa de persistencia.",
    response_description="<ent> encontrado",
    responses={404: {"description": "<ent> no encontrado"}},
)
async def get_<snake_name>(
        <snake_name>_id: uuid.UUID,
        session: AsyncSession = Depends(get_db_session),
):
    return await get_<snake_name>_controller(<snake_name>_id, session)


@router.delete(
    "/{<snake_name>_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar <snake_name> (soft delete)",
    description="Marca un <snake_name> como eliminado de forma logica sin borrarlo fisicamente de la base de datos.",
    responses={
        204: {"description": "<ent> eliminado logicamente"},
        404: {"model": ErrorResponse, "description": "<ent> no encontrado"},
        422: {"description": "Error de validacion de FastAPI"},
    },
)
async def delete_<snake_name>(
        <snake_name>_id: uuid.UUID,
        session: AsyncSession = Depends(get_db_session),
):
    return await delete_<snake_name>_controller(<snake_name>_id, session)
