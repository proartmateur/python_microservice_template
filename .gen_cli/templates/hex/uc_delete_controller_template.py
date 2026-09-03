from uuid import UUID

from src.modules.<snake_name>s.use_cases.delete_<snake_name>s import Delete<ent>s


async def delete_<snake_name>s_controller(
    use_case: Delete<ent>s,
    identifier: UUID,
) -> None:
    await use_case.execute(identifier)
