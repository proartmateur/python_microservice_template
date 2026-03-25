import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.<snake_name>s.infrastructure.persistence.repositories import <ent>Repository
from src.modules.<snake_name>s.infrastructure.http.schemas import (
    <ent>UpdateRequest,
    to_<snake_name>_response,
)


async def update_<snake_name>_controller(
        <snake_name>_id: uuid.UUID,
        payload: <ent>UpdateRequest,
        session: AsyncSession = Depends(get_db_session),
):
    repo = <ent>Repository(session)

    try:
        updated_<snake_name> = await repo.update(
            <snake_name>_id=<snake_name>_id,
(            $camel_prop$=payload.$camel_prop$,
)
        )
    except ValueError as exc:
        message = str(exc)
        if "Ya existe" in message:
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc

    if updated_<snake_name> is None:
        raise HTTPException(status_code=404, detail="<ent> no encontrado")

    return to_<snake_name>_response(updated_<snake_name>)
