from src.shared.domain.errors import AlreadyExistsError, NotFoundError


class ProductNotFoundError(NotFoundError):
    """El product solicitado no existe."""


class ProductAlreadyExistsError(AlreadyExistsError):
    """Ya existe un product con los valores únicos solicitados."""
