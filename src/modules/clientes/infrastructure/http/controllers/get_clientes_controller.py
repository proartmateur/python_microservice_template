from uuid import UUID

from src.modules.clientes.infrastructure.http.schemas import (
    ClienteGetResponse,
    to_cliente_get_response,
)
from src.modules.clientes.use_cases.get_clientes import GetClientes


async def get_clientes_controller(
    use_case: GetClientes,
    identifier: UUID,
) -> ClienteGetResponse:
    return to_cliente_get_response(await use_case.execute(identifier))
