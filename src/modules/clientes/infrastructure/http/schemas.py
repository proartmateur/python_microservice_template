# gencli:schema-imports
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.modules.clientes.domain.entities import ClienteEntity

# gencli:schema-models
class ClienteGetResponse(BaseModel):
    id: UUID
    nombre: str
    email: str
    created_at: datetime
class ClienteResponse(BaseModel):
    id: UUID
    nombre: str
    email: str
    created_at: datetime
# gencli:schema-mappers
def to_cliente_get_response(
    entity: ClienteEntity,
) -> ClienteGetResponse:
    return ClienteGetResponse(
        id=entity.id_cliente,
        nombre=entity.nombre,
        email=entity.email,
        created_at=entity.created_at
    )
def to_cliente_response(
    entity: ClienteEntity,
) -> ClienteResponse:
    return ClienteResponse(
        id=entity.id_cliente,
        nombre=entity.nombre,
        email=entity.email,
        created_at=entity.created_at
    )
