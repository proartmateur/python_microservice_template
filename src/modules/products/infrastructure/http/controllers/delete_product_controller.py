import uuid

from fastapi import Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.persistence.database import get_db_session
from src.modules.products.infrastructure.persistence.repositories import ProductRepository


async def delete_product_controller(
        product_id: uuid.UUID,
        session: AsyncSession = Depends(get_db_session),
):
    repo = ProductRepository(session)
    was_deleted = await repo.soft_delete(product_id)

    if not was_deleted:
        raise HTTPException(status_code=404, detail="Product no encontrado")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
