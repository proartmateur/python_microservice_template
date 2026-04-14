from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- Configuración Base ---
    APP_NAME: str = "Microservicio con GenCLI"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = False
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API REST para modulos del microservicio"
    OPENAPI_URL: str = "/openapi.json"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"

    # --- PostgreSQL (Base Principal) ---
    PG_USER: str
    PG_PASSWORD: str
    PG_HOST: str
    PG_PORT: int = 5432
    PG_DB: str
    PG_SSLMODE: Literal["disable", "require"] = "disable"
    PG_CONNECT_TIMEOUT: int = 10

    @property
    def pg_dsn(self) -> str:
        """Construye la URL de conexión dinámicamente para SQLAlchemy (Async)"""
        base = f"postgresql+asyncpg://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}"
        if self.PG_SSLMODE == "disable":
            base += "?ssl=disable"
        return base

    @property
    def pg_connect_args(self) -> dict[str, object]:
        args: dict[str, object] = {"timeout": float(self.PG_CONNECT_TIMEOUT)}
        if self.PG_SSLMODE == "require":
            import ssl as _ssl
            args["ssl"] = _ssl.create_default_context()
        else:
            # Deshabilitar explícitamente la negociación SSL.
            # asyncpg intenta SSL por defecto; en Windows + Python 3.13
            # esto puede causar "connection was closed in the middle of operation".
            args["ssl"] = False
        return args

    # --- SQL Server (Integración opcional) ---
    MS_USER: Optional[str] = Field(default=None)
    MS_PASSWORD: Optional[str] = Field(default=None)
    MS_HOST: Optional[str] = Field(default=None)
    MS_PORT: int = 1433
    MS_DB: Optional[str] = Field(default=None)
    DB_DRIVER: str = Field(default="ODBC Driver 18 for SQL Server")

    @property
    def ms_driver(self) -> str:
        """Devuelve el driver ODBC a usar: el configurado si está instalado, si no el mejor disponible."""
        import pyodbc
        _FALLBACKS = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server",
        ]
        available = pyodbc.drivers()
        if self.DB_DRIVER in available:
            return self.DB_DRIVER
        for driver in _FALLBACKS:
            if driver in available:
                return driver
        raise RuntimeError(
            f"No se encontró ningún driver ODBC para SQL Server. "
            f"Disponibles: {available}. "
            f"Descarga el driver en: https://aka.ms/downloadmsodbcsql"
        )

    @property
    def ms_dsn(self) -> str:
        """Construye la URL de conexión para SQL Server (Async)"""
        if not all([self.MS_USER, self.MS_PASSWORD, self.MS_HOST, self.MS_DB]):
            raise RuntimeError(
                "Faltan variables de entorno para SQL Server: MS_USER, MS_PASSWORD, MS_HOST, MS_DB"
            )
        driver = self.ms_driver.replace(" ", "+")
        return (
            f"mssql+aioodbc://{self.MS_USER}:{self.MS_PASSWORD}"
            f"@{self.MS_HOST}:{self.MS_PORT}/{self.MS_DB}"
            f"?driver={driver}&TrustServerCertificate=yes"
        )

    # --- Infraestructura de Mensajería y Caché ---
    RABBITMQ_URL: str = Field(default="amqp://guest:guest@localhost:5672/")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # --- Búsqueda (Meilisearch) ---
    MEILISEARCH_URL: str = Field(default="http://localhost:7700")
    MEILISEARCH_MASTER_KEY: Optional[str] = Field(default=None)

    # --- Configuración del Lector ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" # Ignora variables del SO que no nos interesan
    )

@lru_cache
def get_settings() -> Settings:
    """
    Patrón Singleton usando caché.
    Garantiza que el archivo .env se lea y valide UNA SOLA VEZ,
    sin importar cuántas veces importes get_settings() en tu código.
    """
    # BaseSettings resuelve campos requeridos desde entorno/.env en runtime.
    return Settings()  # type: ignore[call-arg]
