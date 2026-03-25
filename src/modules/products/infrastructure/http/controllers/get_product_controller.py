import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.products.infrastructure.persistence.repositories import ProductRepository
from src.modules.products.infrastructure.http.schemas import (
    to_product_response,
)


async def get_product_controller(
        product_id: uuid.UUID,
        session: AsyncSession = Depends(get_db_session),
):
    repo = ProductRepository(session)
    product = await repo.find_by_id(product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product no encontrado")

    return to_product_response(product)
