from typing import Protocol


class UnitOfWork(Protocol):
    """Controla el límite transaccional de un caso de uso."""

    async def commit(self) -> None:
        """Confirma todos los cambios de la operación actual."""

    async def rollback(self) -> None:
        """Revierte todos los cambios de la operación actual."""
