"""Crea la tabla de <ent> y su indice parcial keyset.

Uso:
    uv run poe create_<snake_name>s_table

Requiere REPOSITORY_DATA_SOURCE=database y credenciales PG_* en .env.
La migracion es opcional: el usuario decide cuando ejecutarla.
"""

import asyncio

from sqlalchemy import text

from src.config import get_settings
from src.modules.<snake_name>s.infrastructure.persistence.models import <ent>Model
from src.shared.infrastructure.persistence.database import Base, db_manager


async def main() -> None:
    settings = get_settings()
    if settings.REPOSITORY_DATA_SOURCE != "database":
        raise RuntimeError(
            "create_<snake_name>s_table requiere REPOSITORY_DATA_SOURCE=database."
        )

    db_manager.init_db(settings.pg_dsn, connect_args=settings.pg_connect_args)
    assert db_manager.engine is not None

    async with db_manager.engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[<ent>Model.__table__],  # type: ignore[list-item]
        )
        await conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS ix_<snake_name>s_active_created_id
            ON <snake_name>s (created_at, id_<snake_name>)
            WHERE deleted_at IS NULL
            """
        ))

    await db_manager.close_db()
    print("Tabla <snake_name>s e indice parcial creados correctamente.")


if __name__ == "__main__":
    asyncio.run(main())