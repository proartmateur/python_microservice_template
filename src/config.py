from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- Configuración Base ---
    APP_NAME: str = "Microservicio GenCLI"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = False

    # --- PostgreSQL (Base Principal) ---
    PG_USER: str
    PG_PASSWORD: str
    PG_HOST: str
    PG_PORT: int = 5432
    PG_DB: str
    
    @property
    def pg_dsn(self) -> str:
        """Construye la URL de conexión dinámicamente para SQLAlchemy (Async)"""
        return f"postgresql+asyncpg://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}"

    # --- SQL Server (Integración) ---
    MS_USER: str
    MS_PASSWORD: str
    MS_HOST: str
    MS_PORT: int = 1433
    MS_DB: str
    
    @property
    def ms_dsn(self) -> str:
        """Construye la URL de conexión para SQL Server (Async)"""
        return f"mssql+aioodbc://{self.MS_USER}:{self.MS_PASSWORD}@{self.MS_HOST}:{self.MS_PORT}/{self.MS_DB}?driver=ODBC+Driver+18+for+SQL+Server"

    # --- Infraestructura de Mensajería y Caché ---
    RABBITMQ_URL: str = Field(default="amqp://guest:guest@localhost:5672/")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # --- Búsqueda (Meilisearch) ---
    MEILISEARCH_URL: str = Field(default="http://localhost:7700")
    MEILISEARCH_MASTER_KEY: str

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
    return Settings()