# src/modules/<snake_name>s/infrastructure/http/routers.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.<snake_name>s.infrastructure.persistence.repositories import <ent>Repository
from src.modules.<snake_name>s.infrastructure.http.schemas import <ent>Response, to_<snake_name>_response

router = APIRouter(prefix="/<kebab_name>s", tags=["<ent>s"])


@router.get("/{<kebab_name>}", response_model=<ent>Response)
async def get_<snake_name>(
        <snake_name>: uuid.UUID,
        session: AsyncSession = Depends(get_db_session)  # Inyeccion de la sesion
):
    # Instanciamos el adaptador (repositorio) pasándole la sesión viva
    repo = <ent>Repository(session)

    # Delegamos la búsqueda
    <snake_name> = await repo.find_by_id(<snake_name>)

    if not <snake_name>:
        raise HTTPException(status_code=404, detail="<ent> no encontrado")

    return to_<snake_name>_response(<snake_name>)
