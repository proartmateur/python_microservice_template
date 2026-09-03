from src.shared.domain.errors import AlreadyExistsError, NotFoundError


class <ent>NotFoundError(NotFoundError):
    """El <snake_name> solicitado no existe."""


class <ent>AlreadyExistsError(AlreadyExistsError):
    """Ya existe un <snake_name> con los valores únicos solicitados."""
