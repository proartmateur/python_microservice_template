from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.modules.<snake_name>s.domain.entities import <ent>Entity


class <ent>Response(BaseModel):
    id: UUID
(     $snake_prop$: $prop_type$
)
    created_at: datetime


def to_<snake_name>_response(entity: <ent>Entity) -> <ent>Response:
    return <ent>Response(
        id=entity.id_<snake_name>,
(        $snake_prop$=entity.$snake_prop$,
)
        created_at=entity.created_at,
    )
