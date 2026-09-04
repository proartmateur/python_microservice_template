"""Test unitario del caso de uso custom sales_by_name."""

import pytest

from src.modules.products.use_cases.custom_sales_by_name import (
    CustomSalesByName,
)


class FakeCustomProductRepository:
    """Fake del repositorio custom para tests sin DB."""

    async def sales_by_name(self, *, name: str) -> list[dict[str, object]]:
        return [{"sample_field": "sample_value"}]


@pytest.mark.asyncio
async def test_custom_sales_by_name_returns_rows() -> None:
    repository = FakeCustomProductRepository()
    use_case = CustomSalesByName(repository)
    result = await use_case.execute(name="test")
    assert result.rows is not None
    assert len(result.rows) >= 1
    assert "sample_field" in result.rows[0]
