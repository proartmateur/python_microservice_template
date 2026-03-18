
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

from src.modules.<snake_name>s.domain.entities import <ent>Entity


class <ent>Response(BaseModel):
    id: UUID
(     $camel_prop$: $prop_type$
)


# Explicit mapper keeps HTTP contract decoupled from domain internals.
def to_<snake_name>_response(<snake_name>: <ent>Entity) -> <ent>Response:
    return <ent>Response(
        id=UUID(str(<snake_name>.id_<snake_name>)),
(         $camel_prop$= <snake_name>.$camel_prop$,
)
    )
