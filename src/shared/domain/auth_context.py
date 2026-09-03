from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AuthContext:
    """Contexto de autenticación que viaja hacia los use cases.

    Es la semilla para mitigar BOLA (OWASP API1): todo endpoint con id en
    ruta debe poder consultar el rol/key_id del actor.
    """

    key_id: UUID
    name: str
    role: str
    key_prefix: str