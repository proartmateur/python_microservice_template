from uuid import UUID

from src.modules.<snake_name>s.infrastructure.http.schemas import (
    <ent>UpdateRequest,
    <ent>UpdateResponse,
    to_<snake_name>_update_response,
)
from src.modules.<snake_name>s.use_cases.update_<snake_name>s import Update<ent>s


async def update_<snake_name>s_controller(
    use_case: Update<ent>s,
    identifier: UUID,
    request: <ent>UpdateRequest,
) -> <ent>UpdateResponse:
    entity = await use_case.execute(identifier, **request.model_dump())
    return to_<snake_name>_update_response(entity)
