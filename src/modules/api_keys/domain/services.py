from typing import Protocol


class KeyHasher(Protocol):
    """Puerto criptográfico para hashear y verificar API keys.

    La implementación por defecto es HMAC-SHA256 con pepper.
    Futable futura: Argon2id sin cambiar la interfaz.
    """

    def hash(self, raw_secret: str) -> str:
        """Hashea el secret de la API key → hex digest de 64 chars."""
        ...

    def verify(self, raw_secret: str, key_hash: str) -> bool:
        """Verifica el secret contra el hash (constant-time)."""
        ...