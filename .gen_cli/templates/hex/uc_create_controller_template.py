from src.modules.<snake_name>s.infrastructure.http.schemas import (
    <ent>CreateRequest,
    <ent>CreateResponse,
    to_<snake_name>_create_response,
)
from src.modules.<snake_name>s.use_cases.create_<snake_name>s import Create<ent>s


async def create_<snake_name>s_controller(
    use_case: Create<ent>s,
    request: <ent>CreateRequest,
) -> <ent>CreateResponse:
    entity = await use_case.execute(**request.model_dump())
    return to_<snake_name>_create_response(entity)
