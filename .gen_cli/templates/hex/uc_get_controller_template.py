from uuid import UUID

from src.modules.<snake_name>s.infrastructure.http.schemas import (
    <ent>GetResponse,
    to_<snake_name>_get_response,
)
from src.modules.<snake_name>s.use_cases.get_<snake_name>s import Get<ent>s


async def get_<snake_name>s_controller(
    use_case: Get<ent>s,
    identifier: UUID,
) -> <ent>GetResponse:
    return to_<snake_name>_get_response(await use_case.execute(identifier))
