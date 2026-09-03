import hashlib
import hmac


class HmacKeyHasher:
    """Implementación de KeyHasher con HMAC-SHA256 y pepper.

    El pepper es un secreto de servidor (SECURITY_PEPPER) que se mezcla
    con el secret de la API key antes de hashear. Esto significa que
    incluso si la DB se filtra, las keys no pueden ser verificadas sin
    el pepper.
    """

    def __init__(self, pepper: str) -> None:
        if len(pepper) < 32:
            raise ValueError(
                "SECURITY_PEPPER debe tener al menos 32 caracteres."
            )
        self._pepper = pepper.encode("utf-8")

    def hash(self, raw_secret: str) -> str:
        return hmac.new(
            self._pepper, raw_secret.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def verify(self, raw_secret: str, key_hash: str) -> bool:
        expected = self.hash(raw_secret)
        return hmac.compare_digest(expected, key_hash)