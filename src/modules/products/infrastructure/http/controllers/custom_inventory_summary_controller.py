"""Controller HTTP para el caso de uso custom inventory_summary."""

from __future__ import annotations

from src.modules.products.use_cases.custom_inventory_summary import (
    CustomInventorySummary,
)
from src.modules.products.infrastructure.http.schemas import (
    CustomInventorySummaryResponse,
)

async def custom_inventory_summary_controller(
    use_case: CustomInventorySummary,
) -> CustomInventorySummaryResponse:
    result = await use_case.execute()
    return CustomInventorySummaryResponse(rows=result.rows)
