from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.modules.<snake_name>s.infrastructure.http.controllers.list_<snake_name>s_controller import (
    list_<snake_name>s_controller,
)
from src.modules.<snake_name>s.infrastructure.http.dependencies import get_list_<snake_name>s
from src.modules.<snake_name>s.infrastructure.http.schemas import <ent>Response
from src.modules.<snake_name>s.use_cases.list_<snake_name>s import List<ent>s


router = APIRouter(prefix="/<snake_name>s", tags=["<ent>s"])

# gencli:routes


@router.get("/", response_model=list[<ent>Response])
async def list_<snake_name>s(
    use_case: Annotated[List<ent>s, Depends(get_list_<snake_name>s)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[<ent>Response]:
    return await list_<snake_name>s_controller(use_case, limit=limit)
