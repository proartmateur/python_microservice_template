class DomainError(Exception):
    """Error controlado que representa una regla del dominio."""


class NotFoundError(DomainError):
    """El recurso solicitado no existe o no está disponible."""


class AlreadyExistsError(DomainError):
    """Una operación viola una restricción de unicidad del dominio."""


class DomainValidationError(DomainError):
    """Los datos son sintácticamente válidos, pero violan una regla de negocio."""


class InvalidCursorError(DomainValidationError):
    """El cursor de paginación no se puede verificar o interpretar."""


class PermissionDeniedError(DomainError):
    """El actor autenticado no puede realizar la operación solicitada."""
