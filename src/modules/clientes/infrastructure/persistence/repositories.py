from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.clientes.domain.repositories import ClienteRepository

# gencli:repository-adapter-imports
from uuid import UUID
from src.modules.clientes.domain.entities import ClienteEntity
from src.modules.clientes.infrastructure.persistence.models import ClienteModel

class PostgresClienteRepository(ClienteRepository):
    """Adaptador PostgreSQL del puerto ClienteRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # gencli:repository-adapter-methods
    async def find_by_id(self, identifier: UUID) -> ClienteEntity | None:
        statement = select(ClienteModel).where(
            ClienteModel.id_cliente == identifier,
            ClienteModel.deleted_at.is_(None),
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return ClienteEntity(
                id_cliente=model.id_cliente,
                nombre=model.nombre,
                email=model.email,
                created_at=model.created_at
        )
    async def list(self, *, limit: int) -> list[ClienteEntity]:
        statement = (
            select(ClienteModel)
            .where(ClienteModel.deleted_at.is_(None))
            .order_by(
                ClienteModel.created_at,
                ClienteModel.id_cliente,
            )
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return [
            ClienteEntity(
            id_cliente=db_cliente.id_cliente,
            nombre=db_cliente.nombre,
            email=db_cliente.email,
            created_at=db_cliente.created_at
            )
            for db_cliente in result.scalars()
        ]
