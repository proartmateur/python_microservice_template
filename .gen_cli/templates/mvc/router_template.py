# src/modules/<snake_name>s/infrastructure/http/routers.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.<snake_name>s.infrastructure.http.schemas import (
    ErrorResponse,
    <ent>CreateRequest,
    <ent>Response,
    to_<snake_name>_response,
)
from src.modules.<snake_name>s.infrastructure.persistence.repositories import <ent>Repository
from src.shared.infrastructure.persistence.database import get_db_session

router = APIRouter(prefix="/<kebab_name>s", tags=["<ent>s"])


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
    repo = <ent>Repository(session)

    try:
        <snake_name> = await repo.create(
(            $camel_prop$=payload.$camel_prop$,
)
        )
    except ValueError as exc:
        message = str(exc)
        if "Ya existe" in message:
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc

    return to_<snake_name>_response(<snake_name>)


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
    repo = <ent>Repository(session)
    <snake_name> = await repo.find_by_id(<snake_name>_id)

    if not <snake_name>:
        raise HTTPException(status_code=404, detail="<ent> no encontrado")

    return to_<snake_name>_response(<snake_name>)
