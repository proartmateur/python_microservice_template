"""Caso de uso custom: ejecuta una consulta SQL nativa."""

from __future__ import annotations

from dataclasses import dataclass

from src.modules.products.infrastructure.persistence.custom_repositories import (
    CustomProductRepository,
)



@dataclass(frozen=True)
class CustomSalesByNameResult:
    """Resultado de la consulta custom como lista de diccionarios."""
    rows: list[dict[str, object]]


class CustomSalesByName:
    """Caso de uso que orquesta una consulta SQL nativa via repositorio custom."""

    def __init__(self, repository: CustomProductRepository) -> None:
        self._repository = repository

    async def execute(self, name: str) -> CustomSalesByNameResult:
        rows = await self._repository.sales_by_name(name=name)
        return CustomSalesByNameResult(rows=rows)
