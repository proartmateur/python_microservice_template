from uuid import UUID

from src.modules.products.use_cases.delete_products import DeleteProducts


async def delete_products_controller(
    use_case: DeleteProducts,
    identifier: UUID,
) -> None:
    await use_case.execute(identifier)
