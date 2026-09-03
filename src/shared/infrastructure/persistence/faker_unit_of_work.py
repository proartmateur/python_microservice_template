class FakerUnitOfWork:
    """Adaptador transaccional no-op para modo faker (sin base de datos)."""

    async def commit(self) -> None:
        """No-op: los cambios ya están en memoria."""
        return None

    async def rollback(self) -> None:
        """No-op: no hay transacción que revertir."""
        return None