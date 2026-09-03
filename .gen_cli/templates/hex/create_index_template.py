"""Crea solo el indice parcial keyset para la tabla de <ent>.

Uso:
    uv run poe create_<snake_name>s_index

Util cuando la tabla ya existe pero falta el indice parcial keyset.
Requiere REPOSITORY_DATA_SOURCE=database y credenciales PG_* en .env.
La migracion es opcional: el usuario decide cuando ejecutarla.
"""

import asyncio

from sqlalchemy import text

from src.config import get_settings
from src.shared.infrastructure.persistence.database import db_manager


async def main() -> None:
    settings = get_settings()
    if settings.REPOSITORY_DATA_SOURCE != "database":
        raise RuntimeError(
            "create_<snake_name>s_index requiere REPOSITORY_DATA_SOURCE=database."
        )

    db_manager.init_db(settings.pg_dsn, connect_args=settings.pg_connect_args)
    assert db_manager.engine is not None

    async with db_manager.engine.begin() as conn:
        await conn.execute(text(
            """
            CREATE INDEX IF NOT EXISTS ix_<snake_name>s_active_created_id
            ON <snake_name>s (created_at, id_<snake_name>)
            WHERE deleted_at IS NULL
            """
        ))

    await db_manager.close_db()
    print("Indice parcial ix_<snake_name>s_active_created_id creado correctamente.")


if __name__ == "__main__":
    asyncio.run(main())