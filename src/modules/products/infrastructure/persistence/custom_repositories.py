"""Repositorio custom para consultas SQL nativas de products.

Este repositorio ejecuta SQL directo a PostgreSQL mediante SQLAlchemy ``text()``.
Los parámetros siempre van parameterized (``:param``) para evitar inyección SQL.
"""

# SQL embebido puede exceder el límite de línea; es confianza de desarrollador.
# ruff: noqa: E501

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class CustomProductRepository:
    """Repositorio custom para consultas SQL nativas del módulo Product."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # gencli:custom-repository-methods
    async def sales_by_name(self, *, name: str) -> list[dict[str, object]]:
        """Consulta SQL nativa generada por gen_custom_query."""
        _sql = text("""
            SELECT name, SUM(price) AS total FROM products WHERE name = :name GROUP BY name
        """)
        result = await self._session.execute(_sql, {"name": name})
        return [dict(row) for row in result.mappings().all()]
    async def inventory_summary(self) -> list[dict[str, object]]:
        """Consulta SQL nativa generada por gen_custom_query."""
        _sql = text("""
            SELECT name, COUNT(*) AS total FROM products GROUP BY name
        """)
        result = await self._session.execute(_sql)
        return [dict(row) for row in result.mappings().all()]
