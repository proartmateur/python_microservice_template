import asyncio
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


def _find_project_root(start: Path) -> Path:
    """Busca el root del proyecto por marcador (`pyproject.toml`)."""
    for candidate in start.parents:
        if (candidate / "pyproject.toml").exists():
            return candidate
    raise RuntimeError("No se encontro `pyproject.toml` en los directorios padre.")


PROJECT_ROOT = _find_project_root(Path(__file__).resolve())
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_settings


CHECK_COLUMN_SQL = text(
    """
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'users'
          AND column_name = 'deleted_at'
    )
    """
)

ADD_COLUMN_SQL = text("ALTER TABLE public.users ADD COLUMN deleted_at TIMESTAMPTZ NULL")


async def add_deleted_at_column_if_missing() -> None:
    settings = get_settings()
    engine = create_async_engine(
        settings.pg_dsn,
        connect_args=settings.pg_connect_args,
        pool_pre_ping=True,
    )

    try:
        async with engine.begin() as conn:
            exists = bool(await conn.scalar(CHECK_COLUMN_SQL))
            if exists:
                print("La columna 'deleted_at' ya existe en 'users'.")
                return

            await conn.execute(ADD_COLUMN_SQL)
            print("Columna 'deleted_at' agregada correctamente en 'users'.")
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(add_deleted_at_column_if_missing())


if __name__ == "__main__":
    print("Verificando migracion users.deleted_at...")
    main()

