# src/main.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
import asyncio

from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError

from src.shared.infrastructure.persistence.database import db_manager
from src.config import get_settings
from src.modules.users.infrastructure.http.routers import router as users_router

from src.modules.cosas.infrastructure.http.routers import router as cosas_router
from src.modules.products.infrastructure.http.routers import router as products_router

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    # 1. Cargamos la configuración
    settings = get_settings()
    print(f"🚀 Iniciando {settings.APP_NAME} en modo {settings.ENVIRONMENT}...")

    # 2. Encendemos el motor de base de datos
    print(f"🔌 Conectando a SQL Server en: {settings.MS_HOST}:{settings.MS_PORT}")
    db_manager.init_db(settings.ms_dsn, connect_args={})

    max_retries = 5
    retry_delay_seconds = 2
    for attempt in range(1, max_retries + 1):
        try:
            await db_manager.ping()
            break
        except SQLAlchemyError as exc:
            if attempt == max_retries:
                raise RuntimeError(
                    "No se pudo establecer conexion a SQL Server tras varios intentos. "
                    "Revisa MS_HOST/MS_PORT/MS_DB, credenciales y estado del servidor."
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
        description=settings.API_DESCRIPTION,
        version=settings.API_VERSION,
        debug=settings.DEBUG,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
        openapi_url=settings.OPENAPI_URL,
        lifespan=lifespan
    )

    app.include_router(users_router, prefix="/api/v1")
    app.include_router(products_router, prefix="/api/v1")

    app.include_router(cosas_router, prefix="/api/v1")

    @app.get(
        "/health",
        tags=["System"],
        summary="Health check",
        description="Valida que la API este levantada y devuelve el entorno activo.",
        response_description="Estado basico del servicio",
    )
    async def health_check() -> dict[str, Any]:
        return {
            "status": "ok",
            "environment": settings.ENVIRONMENT,
        }

    return app


app = create_app()