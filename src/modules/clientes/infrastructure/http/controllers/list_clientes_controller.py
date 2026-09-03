from src.modules.clientes.infrastructure.http.schemas import (
    ClienteResponse,
    to_cliente_response,
)
from src.modules.clientes.use_cases.list_clientes import ListClientes


async def list_clientes_controller(
    use_case: ListClientes,
    *,
    limit: int,
) -> list[ClienteResponse]:
    clientes = await use_case.execute(limit=limit)
    return [to_cliente_response(cliente) for cliente in clientes]
