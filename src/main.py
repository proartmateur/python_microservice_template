# src/main.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
import asyncio

from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError

from src.shared.infrastructure.persistence.database import db_manager
from src.config import get_settings
from src.modules.users.infrastructure.http.routers import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    # 1. Cargamos la configuración
    settings = get_settings()
    print(f"🚀 Iniciando {settings.APP_NAME} en modo {settings.ENVIRONMENT}...")

    # 2. Encendemos el motor de base de datos
    print(f"🔌 Conectando a Postgres en: {settings.PG_HOST}:{settings.PG_PORT}")
    db_manager.init_db(settings.pg_dsn, connect_args=settings.pg_connect_args)

    max_retries = 5
    retry_delay_seconds = 2
    for attempt in range(1, max_retries + 1):
        try:
            await db_manager.ping()
            break
        except SQLAlchemyError as exc:
            if attempt == max_retries:
                raise RuntimeError(
                    "No se pudo establecer conexion a PostgreSQL tras varios intentos. "
                    "Revisa PG_HOST/PG_PORT/PG_DB, credenciales, SSL y estado del servidor."
                ) from exc
            print(
                f"⚠️ Intento {attempt}/{max_retries} de conexion fallido. "
                f"Reintentando en {retry_delay_seconds}s..."
            )
            await asyncio.sleep(retry_delay_seconds)

    yield

    # 3. Apagamos el motor y liberamos las conexiones
    print("🛑 Apagando el servicio y cerrando conexiones de DB...")
    await db_manager.close_db()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan
    )

    app.include_router(users_router, prefix="/api/v1")

    @app.get("/health", tags=["System"])
    async def health_check() -> dict[str, Any]:
        return {
            "status": "ok",
            "environment": settings.ENVIRONMENT,
        }

    return app


app = create_app()