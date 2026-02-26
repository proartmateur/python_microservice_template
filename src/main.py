from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Cargamos la configuración de forma segura
    settings = get_settings()
    print(f"🚀 Iniciando {settings.APP_NAME} en modo {settings.ENVIRONMENT}...")
    
    # Aquí es donde, más adelante, usarás settings.pg_dsn para iniciar tu base de datos
    # print(f"Conectando a Postgres en: {settings.PG_HOST}")
    
    yield 
    
    print("🛑 Apagando el servicio...")

def create_app() -> FastAPI:
    settings = get_settings() # Lo llamamos de nuevo, pero gracias a @lru_cache es instantáneo
    
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan
    )

    @app.get("/health", tags=["System"])
    async def health_check():
        # El autocompletado de tu IDE sabrá exactamente qué propiedades tiene `settings`
        return {
            "status": "ok", 
            "environment": settings.ENVIRONMENT,
            "redis_url": settings.REDIS_URL
        }

    return app

app = create_app()