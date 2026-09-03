from src.shared.domain.errors import DomainError, PermissionDeniedError


class InvalidApiKeyError(DomainError):
    """La API key no existe, está malformada o el secret no coincide."""


class ExpiredApiKeyError(DomainError):
    """La API key ha expirado según su campo expires_at."""


class RevokedApiKeyError(DomainError):
    """La API key fue revocada y ya no es válida."""


class InsufficientRoleError(PermissionDeniedError):
    """La API key es válida pero el rol no tiene el permiso requerido."""