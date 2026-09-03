from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.modules.clientes.domain.repositories import ClienteRepository
from src.modules.clientes.infrastructure.persistence.repositories import (
    PostgresClienteRepository,
)
from src.modules.clientes.infrastructure.persistence.faker_repositories import (
    FakerClienteRepository,
    FakerClienteStore,
)
from src.shared.infrastructure.persistence.database import (
    get_optional_db_session,
)

# gencli:use-case-imports
from src.modules.clientes.use_cases.get_clientes import GetClientes
from src.modules.clientes.use_cases.list_clientes import ListClientes

_faker_cliente_store: FakerClienteStore | None = None

def get_faker_cliente_store() -> FakerClienteStore:
    """Provee un store faker singleton por modulo (estado coherente entre requests)."""
    global _faker_cliente_store
    if _faker_cliente_store is None:
        _faker_cliente_store = FakerClienteStore()
    return _faker_cliente_store

def get_cliente_repository(
    session: AsyncSession | None = Depends(get_optional_db_session),
    store: FakerClienteStore = Depends(get_faker_cliente_store),
) -> ClienteRepository:
    """Inyecta el adaptador de persistencia del modulo segun el modo configurado."""
    if get_settings().REPOSITORY_DATA_SOURCE == "faker":
        return FakerClienteRepository(store)
    if session is None:
        raise RuntimeError(
            "La base de datos no ha sido inicializada. Llama a init_db primero."
        )
    return PostgresClienteRepository(session)

# gencli:use-case-providers
def get_get_clientes(
    repository: ClienteRepository = Depends(get_cliente_repository),
) -> GetClientes:
    return GetClientes(repository)
def get_list_clientes(
    repository: ClienteRepository = Depends(
        get_cliente_repository
    ),
) -> ListClientes:
    return ListClientes(repository)