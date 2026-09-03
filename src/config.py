from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
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

    # --- Origen de Datos del Repositorio ---
    # "database": usa PostgreSQL + SQLAlchemy (requiere PG_*).
    # "faker":    usa adaptadores en memoria con datos sintéticos (sin DB).
    REPOSITORY_DATA_SOURCE: Literal["database", "faker"] = "database"

    # --- PostgreSQL (Base Principal) ---
    # Opcionales cuando REPOSITORY_DATA_SOURCE == "faker".
    PG_USER: str | None = None
    PG_PASSWORD: str | None = None
    PG_HOST: str | None = None
    PG_PORT: int = 5432
    PG_DB: str | None = None
    PG_SSLMODE: Literal["disable", "require"] = "disable"
    PG_CONNECT_TIMEOUT: int = 10

    @model_validator(mode="after")
    def _validate_pg_credentials(self) -> "Settings":
        """Exige credenciales PostgreSQL y pepper de seguridad solo en modo database."""
        if self.REPOSITORY_DATA_SOURCE == "database":
            missing = [
                name
                for name in ("PG_USER", "PG_PASSWORD", "PG_HOST", "PG_DB")
                if getattr(self, name) is None
            ]
            if missing:
                raise ValueError(
                    f"REPOSITORY_DATA_SOURCE=database requiere: {', '.join(missing)}"
                )
            if len(self.SECURITY_PEPPER) < 32:
                raise ValueError(
                    "REPOSITORY_DATA_SOURCE=database requiere SECURITY_PEPPER "
                    "de al menos 32 caracteres."
                )
        return self

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

    # --- SQL Server (Integración) ---
    MS_USER: str | None = None
    MS_PASSWORD: str | None = None
    MS_HOST: str | None = None
    MS_PORT: int = 1433
    MS_DB: str | None = None

    @property
    def ms_dsn(self) -> str:
        """Construye la URL de conexión para SQL Server (Async)"""
        if not all((self.MS_USER, self.MS_PASSWORD, self.MS_HOST, self.MS_DB)):
            raise RuntimeError("La configuración de SQL Server está incompleta.")
        return f"mssql+aioodbc://{self.MS_USER}:{self.MS_PASSWORD}@{self.MS_HOST}:{self.MS_PORT}/{self.MS_DB}?driver=ODBC+Driver+18+for+SQL+Server"

    # --- Infraestructura de Mensajería y Caché ---
    RABBITMQ_URL: str = Field(default="amqp://guest:guest@localhost:5672/")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # --- Paginación ---
    # Requerido en modo database para firmar cursores; en modo faker se genera
    # un secret efímero si viene None.
    PAGINATION_CURSOR_SECRET: str | None = Field(default=None, min_length=32)

    # --- Seguridad (API Keys) ---
    # Pepper para HMAC-SHA256 de las API keys. Mínimo 32 bytes.
    # Requerido cuando REPOSITORY_DATA_SOURCE=database.
    # En modo faker se permite un pepper efímero si está vacío.
    SECURITY_PEPPER: str = ""

    # --- Búsqueda (Meilisearch) ---
    MEILISEARCH_URL: str = Field(default="http://localhost:7700")
    MEILISEARCH_MASTER_KEY: str | None = None

    # --- Configuración del Lector ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignora variables del SO que no nos interesan
    )


@lru_cache
def get_settings() -> Settings:
    """
    Patrón Singleton usando caché.
    Garantiza que el archivo .env se lea y valide UNA SOLA VEZ,
    sin importar cuántas veces importes get_settings() en tu código.
    """
    # BaseSettings resuelve campos requeridos desde entorno/.env en runtime.
    return Settings()
