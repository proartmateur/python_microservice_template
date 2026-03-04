# src/modules/users/domain/entities.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid6 import uuid7, UUID


def get_utc_now() -> datetime:
    """Garantiza que el dominio siempre hable en UTC absoluto"""
    return datetime.now(timezone.utc)


@dataclass
class UserEntity:
    # 1. Propiedades obligatorias del negocio
    nombre: str
    email: str

    # 2. Identidad: Se auto-genera con UUIDv7 si nace en la RAM (Caso de Uso),
    # pero puede recibir un UUID existente si viene de Postgres (Repositorio).
    id_user: UUID = field(default_factory=uuid7)

    # 3. Auditoría temporal: Se sella con la hora del servidor en UTC al nacer.
    created_at: datetime = field(default_factory=get_utc_now)

    # Aquí irían los métodos de comportamiento (Domain Logic)
    def update_email(self, new_email: str) -> None:
        if "@" not in new_email:
            raise ValueError("Email inválido")
        self.email = new_email
        # Aquí registraríamos el Domain Event: self.events.append(EmailUpdated(...))