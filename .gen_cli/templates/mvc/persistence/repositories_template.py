import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.<snake_name>s.domain.entities import <ent>Entity
from src.modules.<snake_name>s.infrastructure.persistence.models import <ent>Model


class <ent>Repository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_id(self, <snake_name>_id: uuid.UUID) -> Optional[<ent>Entity]:
        """Busca una entidad por su UUID y devuelve la Entidad de Dominio."""
        stmt = select(<ent>Model).where(<ent>Model.id_<snake_name> == <snake_name>_id)
        result = await self.session.execute(stmt)
        db_<snake_name> = result.scalar_one_or_none()

        if db_<snake_name> is None:
            return None

        return <ent>Entity(
            id_<snake_name>=db_<snake_name>.id_<snake_name>,
(             $camel_prop$=db_<snake_name>.$snake_prop$,
)
            created_at=db_<snake_name>.created_at,
        )

    async def create(
        self,
(        $camel_prop$: $prop_type$,
)
    ) -> <ent>Entity:
        """Crea una entidad nueva y devuelve la entidad de dominio persistida."""
        <snake_name> = <ent>Entity(
(            $camel_prop$=$camel_prop$,
)
        )
        db_<snake_name> = <ent>Model(
            id_<snake_name>=uuid.UUID(str(<snake_name>.id_<snake_name>)),
(            $snake_prop$=<snake_name>.$camel_prop$,
)
            created_at=<snake_name>.created_at,
        )

        self.session.add(db_<snake_name>)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError("Ya existe un <snake_name> con ese valor unico") from exc

        return <snake_name>

