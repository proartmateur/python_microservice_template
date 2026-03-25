from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.modules.<snake_name>s.domain.entities import <ent>Entity


class <ent>Response(BaseModel):
    id: UUID
(     $camel_prop$: $prop_type$
)
    created_at: datetime


class <ent>CreateRequest(BaseModel):
(    $camel_prop$: $prop_type$
)


class <ent>UpdateRequest(BaseModel):
(    $camel_prop$: $prop_type$
)


class ErrorResponse(BaseModel):
    detail: str


class <ent>PaginatedResponse(BaseModel):
    page: int
    total_pages: int
    total_<snake_name>s: int
    limit: int
    has_next: bool
    has_prev: bool
    items: list[<ent>Response]


# Explicit mapper keeps HTTP contract decoupled from domain internals.
def to_<snake_name>_response(<snake_name>: <ent>Entity) -> <ent>Response:
    return <ent>Response(
        id=UUID(str(<snake_name>.id_<snake_name>)),
(        $camel_prop$=<snake_name>.$camel_prop$,
)
        created_at=<snake_name>.created_at,
    )
