import pytest
from uuid import uuid4

from src.modules.users.domain.entities import UserEntity
from src.modules.users.domain.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.modules.users.infrastructure.persistence.faker_repositories import (
    FakerUserRepository,
    FakerUserStore,
)


@pytest.fixture()
def repo() -> FakerUserRepository:
    store = FakerUserStore(seed=42)
    return FakerUserRepository(store)


@pytest.mark.asyncio
async def test_store_seeds_25_entities() -> None:
    store = FakerUserStore(seed=42)
    assert len(store.items) == 25
    assert len(store.deleted_ids) == 0


@pytest.mark.asyncio
async def test_list_returns_only_active(repo: FakerUserRepository) -> None:
    result = await repo.list(limit=100)
    assert len(result) == 25


@pytest.mark.asyncio
async def test_save_and_find_by_id(repo: FakerUserRepository) -> None:
    entity = UserEntity(nombre="TestSave", email="test.save@example.com")
    await repo.save(entity)

    found = await repo.find_by_id(entity.id_user)
    assert found is not None
    assert found.nombre == "TestSave"
    assert found.email == "test.save@example.com"


@pytest.mark.asyncio
async def test_save_duplicate_email_raises(repo: FakerUserRepository) -> None:
    entity = UserEntity(nombre="Dup", email="dup@example.com")
    await repo.save(entity)

    entity2 = UserEntity(nombre="Dup2", email="dup@example.com")
    with pytest.raises(UserAlreadyExistsError):
        await repo.save(entity2)


@pytest.mark.asyncio
async def test_find_by_id_nonexistent_returns_none(
    repo: FakerUserRepository,
) -> None:
    found = await repo.find_by_id(uuid4())
    assert found is None


@pytest.mark.asyncio
async def test_update_modifies_fields(repo: FakerUserRepository) -> None:
    entity = UserEntity(nombre="ToUpdate", email="to.update@example.com")
    await repo.save(entity)

    updated = await repo.update(
        entity.id_user, nombre="UpdatedName", email="updated.email@example.com"
    )
    assert updated.nombre == "UpdatedName"
    assert updated.email == "updated.email@example.com"


@pytest.mark.asyncio
async def test_update_nonexistent_raises(repo: FakerUserRepository) -> None:
    with pytest.raises(UserNotFoundError):
        await repo.update(uuid4(), nombre="x", email="x@example.com")


@pytest.mark.asyncio
async def test_soft_delete_marks_as_deleted(repo: FakerUserRepository) -> None:
    entity = UserEntity(nombre="ToDelete", email="to.delete@example.com")
    await repo.save(entity)

    await repo.soft_delete(entity.id_user)

    found = await repo.find_by_id(entity.id_user)
    assert found is None
    active = await repo.list(limit=100)
    assert all(e.id_user != entity.id_user for e in active)


@pytest.mark.asyncio
async def test_soft_delete_nonexistent_raises(repo: FakerUserRepository) -> None:
    with pytest.raises(UserNotFoundError):
        await repo.soft_delete(uuid4())


@pytest.mark.asyncio
async def test_list_paginated_keyset(repo: FakerUserRepository) -> None:
    page1 = await repo.list_paginated(limit=10, cursor=None)
    assert len(page1.items) == 10
    assert page1.has_next is True
    assert page1.next_position is not None

    page2 = await repo.list_paginated(limit=10, cursor=page1.next_position)
    assert len(page2.items) == 10
    # No debe haber solapamiento entre páginas.
    page1_ids = {e.id_user for e in page1.items}
    page2_ids = {e.id_user for e in page2.items}
    assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_find_by_equals(repo: FakerUserRepository) -> None:
    from src.shared.domain.find_by import FindByCriteria, FindByOperator

    entity = UserEntity(nombre="ExactMatch", email="exact@example.com")
    await repo.save(entity)

    result = await repo.find_by(
        criteria=FindByCriteria(
            field="nombre",
            operator=FindByOperator.EQUALS,
            value="ExactMatch",
        ),
        limit=10,
        cursor=None,
        pagination=False,
    )
    assert any(e.nombre == "ExactMatch" for e in result.items)