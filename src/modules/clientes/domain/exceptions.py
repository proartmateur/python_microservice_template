from src.shared.domain.errors import AlreadyExistsError, NotFoundError


class ClienteNotFoundError(NotFoundError):
    """El cliente solicitado no existe."""


class ClienteAlreadyExistsError(AlreadyExistsError):
    """Ya existe un cliente con los valores únicos solicitados."""
