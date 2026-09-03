import re
import secrets
from dataclasses import dataclass
from enum import StrEnum

_PREFIX_RE = re.compile(r"^pk_[0-9a-f]{8}$")  # pk_a1b2c3d4 (11 chars)
_FULL_RE = re.compile(r"^pk_[0-9a-f]{8}_[A-Za-z0-9_-]{43,}$")


class KeyStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"


@dataclass(frozen=True)
class KeyPrefix:
    """Prefijo de 12 chars de la API key (p.ej. pk_a1b2c3d4)."""

    value: str

    def __post_init__(self) -> None:
        if not _PREFIX_RE.match(self.value):
            raise ValueError(
                f"KeyPrefix inválido: {self.value!r}. "
                "Formato esperado: pk_<8 hex chars>."
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class KeyHash:
    """Hash HMAC-SHA256 en hex (64 chars). Nunca se loguea ni se devuelve."""

    value: str

    def __post_init__(self) -> None:
        if len(self.value) != 64 or not all(
            c in "0123456789abcdef" for c in self.value
        ):
            raise ValueError(
                "KeyHash inválido: debe ser 64 chars hex (HMAC-SHA256)."
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RawApiKey:
    """Wrapper de la clave en claro. Solo vive en RAM.

    Se devuelve UNA sola vez en creación/rotación. Nunca se persiste
    ni se loguea.
    """

    value: str

    def __post_init__(self) -> None:
        if not _FULL_RE.match(self.value):
            raise ValueError(
                "RawApiKey inválida. Formato esperado: "
                "pk_<8hex>_<43+ chars urlsafe>."
            )

    @classmethod
    def generate(cls) -> "RawApiKey":
        """Genera una clave con 256+ bits de entropía."""
        short_id = secrets.token_hex(4)
        secret = secrets.token_urlsafe(32)
        return cls(f"pk_{short_id}_{secret}")

    @property
    def prefix(self) -> KeyPrefix:
        return KeyPrefix(self.value[:11])

    @property
    def secret(self) -> str:
        return self.value[12:]

    def __str__(self) -> str:
        return self.value