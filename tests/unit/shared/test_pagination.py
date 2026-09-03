from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.shared.domain.errors import InvalidCursorError
from src.shared.domain.pagination import KeysetCursor
from src.shared.infrastructure.http.pagination import HmacCursorCodec


def test_cursor_codec_round_trip() -> None:
    codec = HmacCursorCodec("a" * 32)
    cursor = KeysetCursor(datetime(2026, 1, 1, tzinfo=UTC), uuid4())

    encoded = codec.encode(cursor)

    assert codec.decode(encoded) == cursor


def test_cursor_codec_rejects_a_tampered_token() -> None:
    codec = HmacCursorCodec("a" * 32)
    cursor = KeysetCursor(datetime(2026, 1, 1, tzinfo=UTC), uuid4())
    encoded = codec.encode(cursor)
    tampered = f"{encoded[:-1]}{'A' if encoded[-1] != 'A' else 'B'}"

    with pytest.raises(InvalidCursorError):
        codec.decode(tampered)


def test_cursor_codec_requires_a_strong_secret() -> None:
    with pytest.raises(ValueError, match="al menos 32"):
        HmacCursorCodec("short")
