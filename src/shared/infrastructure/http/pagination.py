import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime
from uuid import UUID

from src.shared.domain.errors import InvalidCursorError
from src.shared.domain.pagination import KeysetCursor


class HmacCursorCodec:
    """Token firmado que evita la manipulación del cursor keyset por clientes."""

    def __init__(self, secret: str) -> None:
        if len(secret) < 32:
            raise ValueError(
                "PAGINATION_CURSOR_SECRET debe tener al menos 32 caracteres."
            )
        self._secret = secret.encode("utf-8")

    def encode(self, cursor: KeysetCursor) -> str:
        payload = json.dumps(
            {
                "created_at": cursor.created_at.astimezone(UTC).isoformat(),
                "id": str(cursor.identifier),
                "v": 1,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        signature = hmac.new(self._secret, payload, hashlib.sha256).digest()
        return f"{self._encode(payload)}.{self._encode(signature)}"

    def decode(self, value: str) -> KeysetCursor:
        try:
            encoded_payload, encoded_signature = value.split(".")
            payload = self._decode(encoded_payload)
            signature = self._decode(encoded_signature)
        except (ValueError, TypeError) as exc:
            raise InvalidCursorError("El cursor de paginación es inválido.") from exc

        expected_signature = hmac.new(self._secret, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected_signature):
            raise InvalidCursorError("El cursor de paginación es inválido.")

        try:
            data = json.loads(payload)
            created_at = datetime.fromisoformat(data["created_at"])
            identifier = UUID(data["id"])
            if data["v"] != 1 or created_at.tzinfo is None:
                raise ValueError
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidCursorError("El cursor de paginación es inválido.") from exc
        return KeysetCursor(
            created_at=created_at.astimezone(UTC), identifier=identifier
        )

    @staticmethod
    def _encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    @staticmethod
    def _decode(value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.b64decode(value + padding, altchars=b"-_", validate=True)
