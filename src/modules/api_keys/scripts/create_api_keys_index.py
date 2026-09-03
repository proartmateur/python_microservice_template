"""Crea solo el indice parcial para la tabla de ApiKey.

Uso:
    uv run poe create_api_keys_index

Util cuando la tabla ya existe pero falta el indice parcial.
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
            "create_api_keys_index requiere REPOSITORY_DATA_SOURCE=database."
        )

    db_manager.init_db(settings.pg_dsn, connect_args=settings.pg_connect_args)
    assert db_manager.engine is not None

    async with db_manager.engine.begin() as conn:
        await conn.execute(text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ix_api_keys_prefix
            ON api_keys (key_prefix)
            WHERE status = 'active'
            """
        ))

    await db_manager.close_db()
    print("Indice parcial ix_api_keys_prefix creado correctamente.")


if __name__ == "__main__":
    asyncio.run(main())