from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.<snake_name>s.infrastructure.persistence.repositories import <ent>Repository
from src.modules.<snake_name>s.infrastructure.http.schemas import (
    <ent>PaginatedResponse,
    to_<snake_name>_response,
)


async def list_<snake_name>s_controller(
        limit: int = Query(default=5, ge=1, description="Cantidad maxima de registros por pagina"),
        page: int = Query(default=0, ge=0, description="Indice de pagina (base 0)"),
        session: AsyncSession = Depends(get_db_session),
):
    repo = <ent>Repository(session)

    try:
        <snake_name>s, total_<snake_name>s, total_pages = await repo.list_paginated(limit=limit, page=page)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    has_prev = page > 0
    has_next = (page + 1) < total_pages

    return <ent>PaginatedResponse(
        page=page,
        total_pages=total_pages,
        total_<snake_name>s=total_<snake_name>s,
        limit=limit,
        has_next=has_next,
        has_prev=has_prev,
        items=[to_<snake_name>_response(<snake_name>) for <snake_name> in <snake_name>s],
    )
