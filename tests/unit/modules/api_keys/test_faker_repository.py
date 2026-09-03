import pytest

from src.modules.api_keys.infrastructure.persistence.faker_repositories import (
    FakerApiKeyRepository,
    FakerApiKeyStore,
)
from src.modules.api_keys.domain.entities import ApiKeyEntity
from uuid import uuid4


@pytest.fixture()
def repo() -> FakerApiKeyRepository:
    store = FakerApiKeyStore(seed=42)
    return FakerApiKeyRepository(store)


@pytest.mark.asyncio
async def test_store_seeds_3_entities() -> None:
    store = FakerApiKeyStore(seed=42)
    assert len(store.items) == 3
    roles = {e.role for e in store.items}
    assert roles == {"admin", "write", "read"}


@pytest.mark.asyncio
async def test_find_by_prefix_returns_entity(
    repo: FakerApiKeyRepository,
) -> None:
    result = await repo.find_by_prefix("pk_00000000")
    assert result is not None
    assert result.role == "admin"


@pytest.mark.asyncio
async def test_find_by_prefix_nonexistent_returns_none(
    repo: FakerApiKeyRepository,
) -> None:
    assert await repo.find_by_prefix("pk_zzzzzzzz") is None


@pytest.mark.asyncio
async def test_save_and_find_by_id(
    repo: FakerApiKeyRepository,
) -> None:
    entity = ApiKeyEntity(
        name="test-save",
        key_prefix="pk_abcdef01",
        key_hash="a" * 64,
        role="read",
        status="active",
    )
    await repo.save(entity)
    found = await repo.find_by_id(entity.id_api_key)
    assert found is not None
    assert found.name == "test-save"


@pytest.mark.asyncio
async def test_revoke_marks_as_revoked(
    repo: FakerApiKeyRepository,
) -> None:
    entity = ApiKeyEntity(
        name="test-revoke",
        key_prefix="pk_12345678",
        key_hash="b" * 64,
        role="write",
        status="active",
    )
    await repo.save(entity)
    await repo.revoke(entity.id_api_key)
    assert entity.status == "revoked"
    assert entity.revoked_at is not None
    found = await repo.find_by_prefix("pk_12345678")
    assert found is None


@pytest.mark.asyncio
async def test_update_hash_changes_prefix_and_hash(
    repo: FakerApiKeyRepository,
) -> None:
    entity = ApiKeyEntity(
        name="test-rotate",
        key_prefix="pk_11111111",
        key_hash="c" * 64,
        role="read",
        status="active",
    )
    await repo.save(entity)
    await repo.update_hash(entity.id_api_key, "d" * 64, "pk_22222222")
    assert entity.key_hash == "d" * 64
    assert entity.key_prefix == "pk_22222222"
    found = await repo.find_by_prefix("pk_22222222")
    assert found is not None


@pytest.mark.asyncio
async def test_revoke_nonexistent_raises(
    repo: FakerApiKeyRepository,
) -> None:
    with pytest.raises(ValueError, match="not found"):
        await repo.revoke(uuid4())