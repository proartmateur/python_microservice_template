from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Protocol, TypeVar
from uuid import UUID


T = TypeVar("T")


@dataclass(frozen=True)
class KeysetCursor:
    """Posición estable para avanzar en una colección ordenada."""

    created_at: datetime
    identifier: UUID


@dataclass(frozen=True)
class CursorPage(Generic[T]):
    """Resultado de una consulta keyset, sin exponer detalles del ORM."""

    items: list[T]
    next_position: KeysetCursor | None
    has_next: bool


class CursorCodec(Protocol):
    """Codifica y verifica posiciones de paginación para el transporte HTTP."""

    def encode(self, cursor: KeysetCursor) -> str: ...

    def decode(self, value: str) -> KeysetCursor: ...
