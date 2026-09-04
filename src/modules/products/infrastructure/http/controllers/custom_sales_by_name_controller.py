"""Controller HTTP para el caso de uso custom sales_by_name."""

from __future__ import annotations

from src.modules.products.use_cases.custom_sales_by_name import (
    CustomSalesByName,
)
from src.modules.products.infrastructure.http.schemas import (
    CustomSalesByNameRequest,
    CustomSalesByNameResponse,
)

async def custom_sales_by_name_controller(
    use_case: CustomSalesByName,
    request: CustomSalesByNameRequest,
) -> CustomSalesByNameResponse:
    result = await use_case.execute(name=request.name)
    return CustomSalesByNameResponse(rows=result.rows)
