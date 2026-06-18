"""Global error handlers for FastAPI.

Maps Contraduria exceptions to HTTP responses with structured error format.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ContraduriaError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)


async def contraduria_error_handler(
    request: Request, exc: ContraduriaError
) -> JSONResponse:
    """Fallback handler for any ContraduriaError."""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "error_code": "INTERNAL_ERROR"},
    )


async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle NotFoundError → 404."""
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "error_code": "NOT_FOUND"},
    )


async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Handle DatabaseError → 503."""
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc), "error_code": "DATABASE_ERROR"},
    )


async def validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle ValidationError → 422."""
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "error_code": "VALIDATION_ERROR"},
    )


def register_error_handlers(app):
    """Registra todos los exception handlers en la aplicación FastAPI."""
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(ContraduriaError, contraduria_error_handler)
