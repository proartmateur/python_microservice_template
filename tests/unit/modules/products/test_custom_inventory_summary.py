"""Test unitario del caso de uso custom inventory_summary."""

import pytest

from src.modules.products.use_cases.custom_inventory_summary import (
    CustomInventorySummary,
)


class FakeCustomProductRepository:
    """Fake del repositorio custom para tests sin DB."""

    async def inventory_summary(self) -> list[dict[str, object]]:
        return [{"sample_field": "sample_value"}]


@pytest.mark.asyncio
async def test_custom_inventory_summary_returns_rows() -> None:
    repository = FakeCustomProductRepository()
    use_case = CustomInventorySummary(repository)
    result = await use_case.execute()
    assert result.rows is not None
    assert len(result.rows) >= 1
    assert "sample_field" in result.rows[0]
