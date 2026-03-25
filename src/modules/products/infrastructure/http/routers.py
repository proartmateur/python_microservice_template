import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.products.infrastructure.http.controllers.create_product_controller import create_product_controller
from src.modules.products.infrastructure.http.controllers.get_product_controller import get_product_controller
from src.modules.products.infrastructure.http.controllers.list_products_controller import list_products_controller
from src.modules.products.infrastructure.http.controllers.update_product_controller import update_product_controller
from src.modules.products.infrastructure.http.controllers.delete_product_controller import delete_product_controller
from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.products.infrastructure.http.schemas import (
    ErrorResponse,
    ProductCreateRequest,
    ProductPaginatedResponse,
    ProductResponse,
    ProductUpdateRequest,
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.get(
    "/",
    response_model=ProductPaginatedResponse,
    summary="Listar products paginados",
    description="Lista products aplicando paginacion por numero de pagina y limite de resultados.",
    response_description="Products paginados",
    responses={
        400: {"model": ErrorResponse, "description": "Parametros de paginacion invalidos"},
        422: {"description": "Error de validacion de FastAPI"},
    },
)
async def list_products(
        limit: int = Query(default=5, ge=1, description="Cantidad maxima de registros por pagina"),
        page: int = Query(default=0, ge=0, description="Indice de pagina (base 0)"),
        session: AsyncSession = Depends(get_db_session),
):
    return await list_products_controller(limit, page, session)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear product",
    description="Crea un nuevo product y lo persiste en la base de datos.",
    response_description="Product creado",
    responses={
        400: {"model": ErrorResponse, "description": "Datos de entrada inválidos"},
        409: {"model": ErrorResponse, "description": "Conflicto por restricción única"},
        422: {"description": "Error de validación de FastAPI"},
    },
)
async def create_product(
        payload: ProductCreateRequest,
        session: AsyncSession = Depends(get_db_session),
):
    return await create_product_controller(payload, session)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Actualizar product",
    description="Actualiza un product existente por UUID.",
    response_description="Product actualizado",
    responses={
        400: {"model": ErrorResponse, "description": "Datos de entrada inválidos"},
        404: {"model": ErrorResponse, "description": "Product no encontrado"},
        409: {"model": ErrorResponse, "description": "Conflicto por restricción única"},
        422: {"description": "Error de validación de FastAPI"},
    },
)
async def update_product(
        product_id: uuid.UUID,
        payload: ProductUpdateRequest,
        session: AsyncSession = Depends(get_db_session),
):
    return await update_product_controller(product_id, payload, session)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Obtener product por ID",
    description="Recupera un product por UUID desde la capa de persistencia.",
    response_description="Product encontrado",
    responses={404: {"description": "Product no encontrado"}},
)
async def get_product(
        product_id: uuid.UUID,
        session: AsyncSession = Depends(get_db_session),
):
    return await get_product_controller(product_id, session)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar product (soft delete)",
    description="Marca un product como eliminado de forma logica sin borrarlo fisicamente de la base de datos.",
    responses={
        204: {"description": "Product eliminado logicamente"},
        404: {"model": ErrorResponse, "description": "Product no encontrado"},
        422: {"description": "Error de validacion de FastAPI"},
    },
)
async def delete_product(
        product_id: uuid.UUID,
        session: AsyncSession = Depends(get_db_session),
):
    return await delete_product_controller(product_id, session)
