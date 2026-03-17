import asyncio
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine


def _find_project_root(start: Path) -> Path:
    """Busca el root del proyecto por marcador (`pyproject.toml`)."""
    for candidate in start.parents:
        if (candidate / "pyproject.toml").exists():
            return candidate
    raise RuntimeError("No se encontro `pyproject.toml` en los directorios padre.")


# Permite ejecutar este script directamente sin depender de PYTHONPATH.
PROJECT_ROOT = _find_project_root(Path(__file__).resolve())
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_settings
from src.modules.petras.infrastructure.persistence.models import PetraModel
from src.shared.infrastructure.persistence.database import Base


async def create_petras_table_if_missing() -> None:
    settings = get_settings()

    engine = create_async_engine(
        settings.pg_dsn,
        connect_args=settings.pg_connect_args,
        pool_pre_ping=True,
    )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(
                    sync_conn,
                    tables=[PetraModel.__table__],
                    checkfirst=True,
                )
            )
        print("Tabla 'petras' verificada/creada correctamente.")
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(create_petras_table_if_missing())


if __name__ == "__main__":
    print("Creando tabla Petras...")
    main()
    print("Tabla creada!")