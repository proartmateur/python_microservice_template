import pytest

from src.modules.api_keys.domain.entities import ApiKeyEntity
from src.modules.api_keys.domain.value_objects import RawApiKey
from src.shared.domain.auth_context import AuthContext


class TestApiKeyEntity:
    def test_entity_has_all_fields(self) -> None:
        raw = RawApiKey.generate()
        entity = ApiKeyEntity(
            name="TestClient",
            key_prefix=raw.prefix.value,
            key_hash="a" * 64,
            role="write",
            status="active",
        )
        assert entity.name == "TestClient"
        assert entity.key_prefix == raw.prefix.value
        assert entity.role == "write"
        assert entity.status == "active"
        assert entity.id_api_key is not None
        assert entity.created_at is not None
        assert entity.expires_at is None
        assert entity.revoked_at is None
        assert entity.last_used_at is None


class TestAuthContext:
    def test_auth_context_is_frozen(self) -> None:
        ctx = AuthContext(
            key_id=entity_id(),
            name="admin",
            role="admin",
            key_prefix="pk_a1b2c3d4",
        )
        with pytest.raises(AttributeError):
            ctx.role = "read"  # type: ignore[misc]

    def test_auth_context_fields(self) -> None:
        ctx = AuthContext(
            key_id=entity_id(),
            name="client1",
            role="write",
            key_prefix="pk_a1b2c3d4",
        )
        assert ctx.name == "client1"
        assert ctx.role == "write"
        assert ctx.key_prefix == "pk_a1b2c3d4"


def entity_id() -> object:
    from uuid6 import uuid7
    return uuid7()