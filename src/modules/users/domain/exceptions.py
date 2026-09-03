from src.shared.domain.errors import AlreadyExistsError, NotFoundError


class UserNotFoundError(NotFoundError):
    """El user solicitado no existe."""


class UserAlreadyExistsError(AlreadyExistsError):
    """Ya existe un user con los valores únicos solicitados."""
