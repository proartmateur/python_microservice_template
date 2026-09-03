from typing import Annotated

from fastapi import APIRouter, Depends, Query

# gencli:router-imports
from uuid import UUID

from .controllers.get_clientes_controller import get_clientes_controller
from src.modules.clientes.infrastructure.http.dependencies import (
    get_get_clientes,
    get_list_clientes,
)
from src.modules.clientes.infrastructure.http.schemas import (
    ClienteGetResponse,
    ClienteResponse,
)
from src.modules.clientes.use_cases.get_clientes import GetClientes
from .controllers.list_clientes_controller import list_clientes_controller
from src.modules.clientes.use_cases.list_clientes import ListClientes

router = APIRouter(prefix="/clientes", tags=["Clientes"])

# gencli:routes
@router.get("/", response_model=list[ClienteResponse])
async def list_clientes(
    use_case: Annotated[
        ListClientes,
        Depends(get_list_clientes),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ClienteResponse]:
    return await list_clientes_controller(use_case, limit=limit)

@router.get("/{identifier}", response_model=ClienteGetResponse)
async def get_clientes(
    identifier: UUID,
    use_case: Annotated[GetClientes, Depends(get_get_clientes)],
) -> ClienteGetResponse:
    return await get_clientes_controller(use_case, identifier)
