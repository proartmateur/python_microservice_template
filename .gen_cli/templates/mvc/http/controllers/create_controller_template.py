from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.<snake_name>s.infrastructure.persistence.repositories import <ent>Repository
from src.modules.<snake_name>s.infrastructure.http.schemas import (
    <ent>CreateRequest,
    to_<snake_name>_response,
)


async def create_<snake_name>_controller(
        payload: <ent>CreateRequest,
        session: AsyncSession = Depends(get_db_session),
):
    repo = <ent>Repository(session)

    try:
        <snake_name> = await repo.create(
(            $camel_prop$=payload.$camel_prop$,
)
        )
    except ValueError as exc:
        message = str(exc)
        if "Ya existe" in message:
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc

    return to_<snake_name>_response(<snake_name>)
