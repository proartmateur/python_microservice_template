from src.modules.<snake_name>s.infrastructure.http.schemas import (
    <ent>Response,
    to_<snake_name>_response,
)
from src.modules.<snake_name>s.use_cases.list_<snake_name>s import List<ent>s


async def list_<snake_name>s_controller(
    use_case: List<ent>s,
    *,
    limit: int,
) -> list[<ent>Response]:
    <snake_name>s = await use_case.execute(limit=limit)
    return [to_<snake_name>_response(<snake_name>) for <snake_name> in <snake_name>s]
