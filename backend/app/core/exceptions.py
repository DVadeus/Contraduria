"""Custom exception hierarchy for Contraduria API.

Each exception maps to a specific HTTP status code via error handlers.
"""


class ContraduriaError(Exception):
    """Base exception for all Contraduria errors."""


class NotFoundError(ContraduriaError):
    """Recurso no encontrado."""


class DatabaseError(ContraduriaError):
    """Error de consulta o conexión a DuckDB."""


class ValidationError(ContraduriaError):
    """Parámetros de entrada inválidos."""
