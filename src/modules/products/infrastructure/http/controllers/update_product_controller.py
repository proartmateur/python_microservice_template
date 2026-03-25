import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.products.infrastructure.persistence.repositories import ProductRepository
from src.modules.products.infrastructure.http.schemas import (
    ProductUpdateRequest,
    to_product_response,
)


async def update_product_controller(
        product_id: uuid.UUID,
        payload: ProductUpdateRequest,
        session: AsyncSession = Depends(get_db_session),
):
    repo = ProductRepository(session)

    try:
        updated_product = await repo.update(
            product_id=product_id,
           name=payload.name,
           user=payload.user,
           isPhisical=payload.isPhisical,

        )
    except ValueError as exc:
        message = str(exc)
        if "Ya existe" in message:
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc

    if updated_product is None:
        raise HTTPException(status_code=404, detail="Product no encontrado")

    return to_product_response(updated_product)
