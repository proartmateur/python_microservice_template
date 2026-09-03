from uuid import UUID

from src.modules.users.use_cases.delete_users import DeleteUsers


async def delete_users_controller(
    use_case: DeleteUsers,
    identifier: UUID,
) -> None:
    await use_case.execute(identifier)
