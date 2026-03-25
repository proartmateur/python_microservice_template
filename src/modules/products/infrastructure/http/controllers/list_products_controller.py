from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.products.infrastructure.persistence.repositories import ProductRepository
from src.modules.products.infrastructure.http.schemas import (
    ProductPaginatedResponse,
    to_product_response,
)


async def list_products_controller(
        limit: int = Query(default=5, ge=1, description="Cantidad maxima de registros por pagina"),
        page: int = Query(default=0, ge=0, description="Indice de pagina (base 0)"),
        session: AsyncSession = Depends(get_db_session),
):
    repo = ProductRepository(session)

    try:
        products, total_products, total_pages = await repo.list_paginated(limit=limit, page=page)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    has_prev = page > 0
    has_next = (page + 1) < total_pages

    return ProductPaginatedResponse(
        page=page,
        total_pages=total_pages,
        total_products=total_products,
        limit=limit,
        has_next=has_next,
        has_prev=has_prev,
        items=[to_product_response(product) for product in products],
    )
