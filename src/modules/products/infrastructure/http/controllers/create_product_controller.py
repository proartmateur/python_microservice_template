from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.products.infrastructure.persistence.repositories import ProductRepository
from src.modules.products.infrastructure.http.schemas import (
    ProductCreateRequest,
    to_product_response,
)


async def create_product_controller(
        payload: ProductCreateRequest,
        session: AsyncSession = Depends(get_db_session),
):
    repo = ProductRepository(session)

    try:
        product = await repo.create(
           name=payload.name,
           user=payload.user,
           isPhisical=payload.isPhisical,

        )
    except ValueError as exc:
        message = str(exc)
        if "Ya existe" in message:
            raise HTTPException(status_code=409, detail=message) from exc
        raise HTTPException(status_code=400, detail=message) from exc

    return to_product_response(product)
