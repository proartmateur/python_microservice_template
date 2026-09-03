from src.modules.<snake_name>s.infrastructure.http.schemas import (
    <ent>FindByRequest,
    <ent>FindByResponse,
    to_<snake_name>_find_by_item_response,
)
from src.modules.<snake_name>s.use_cases.find_by_<snake_name>s import FindBy<ent>s


async def find_by_<snake_name>s_controller(
    use_case: FindBy<ent>s,
    request: <ent>FindByRequest,
) -> <ent>FindByResponse:
    result = await use_case.execute(
        criteria=request.to_criteria(),
        limit=request.limit,
        cursor=request.cursor,
        pagination=request.pagination,
    )
    return <ent>FindByResponse(
        items=[to_<snake_name>_find_by_item_response(item) for item in result.items],
        next_cursor=result.next_cursor,
        has_next=result.has_next,
        limit=request.limit,
    )
