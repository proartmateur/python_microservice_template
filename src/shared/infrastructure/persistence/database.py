from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


# 1. La clase Base para tus modelos de SQLAlchemy
class Base(DeclarativeBase):
    pass


# 2. El Administrador (Singleton)
class DatabaseManager:
    def __init__(self) -> None:
        self.engine: AsyncEngine | None = None
        self.session_maker: async_sessionmaker[AsyncSession] | None = None

    def init_db(self, db_url: str, *, connect_args: dict[str, object] | None = None) -> None:
        """Inicializa el pool de conexiones. Se llama al arrancar FastAPI."""
        # pool_pre_ping ayuda cuando el servidor cierra conexiones inactivas.
        self.engine = create_async_engine(
            db_url,
            connect_args=connect_args or {},
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_timeout=30,
            echo=False,
        )

        self.session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def ping(self) -> None:
        """Valida conectividad al motor con una consulta minima."""
        if self.engine is None:
            raise RuntimeError("La base de datos no ha sido inicializada. Llama a init_db primero.")

        async with self.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def close_db(self) -> None:
        """Cierra el pool ordenadamente. Se llama al apagar FastAPI."""
        if self.engine is not None:
            await self.engine.dispose()


# 3. La instancia global única (Tu Singleton real)
db_manager = DatabaseManager()


# 4. Inyección de dependencias para los Repositorios o Casos de Uso
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Generador que provee una sesión única por cada petición HTTP."""
    if db_manager.session_maker is None:
        raise RuntimeError("La base de datos no ha sido inicializada. Llama a init_db primero.")

    async with db_manager.session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()