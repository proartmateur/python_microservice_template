import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.shared.domain.errors import (
    AlreadyExistsError,
    DomainError,
    DomainValidationError,
    NotFoundError,
    PermissionDeniedError,
)

logger = logging.getLogger(__name__)


def _problem_response(
    request: Request,
    *,
    status_code: int,
    title: str,
    detail: str,
    problem_type: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "type": f"https://api.example.invalid/problems/{problem_type}",
            "title": title,
            "status": status_code,
            "detail": detail,
            "instance": request.url.path,
        },
        media_type="application/problem+json",
    )


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convierte errores de dominio en respuestas RFC 9457 sin detalles internos."""
    if isinstance(exc, NotFoundError):
        return _problem_response(
            request,
            status_code=404,
            title="Recurso no encontrado",
            detail=str(exc),
            problem_type="not-found",
        )
    if isinstance(exc, AlreadyExistsError):
        return _problem_response(
            request,
            status_code=409,
            title="Conflicto de recurso",
            detail=str(exc),
            problem_type="already-exists",
        )
    if isinstance(exc, DomainValidationError):
        return _problem_response(
            request,
            status_code=400,
            title="Regla de negocio inválida",
            detail=str(exc),
            problem_type="validation",
        )
    if isinstance(exc, PermissionDeniedError):
        return _problem_response(
            request,
            status_code=403,
            title="Acceso denegado",
            detail="No tiene permiso para realizar esta operación.",
            problem_type="permission-denied",
        )
    return _problem_response(
        request,
        status_code=400,
        title="Error de dominio",
        detail="Ocurrió un error de dominio.",
        problem_type="domain-error",
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Evita filtrar detalles internos y preserva la causa en logs del servidor."""
    logger.exception("Unhandled exception for %s", request.url.path, exc_info=exc)
    return _problem_response(
        request,
        status_code=500,
        title="Error interno del servidor",
        detail="Ocurrió un error inesperado.",
        problem_type="internal-error",
    )


def register_error_handlers(app: FastAPI) -> None:
    """Registra los handlers compartidos una sola vez en el composition root."""
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
