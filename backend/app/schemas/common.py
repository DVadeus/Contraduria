"""Common Pydantic schemas shared across all API endpoints.

Incluye:
- PaginationParams, PaginatedResponse (genéricos)
- ErrorResponse, HealthResponse
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class PaginationParams(BaseModel):
    """Parámetros de paginación estándar."""

    page: int = Field(default=1, ge=1, description="Número de página (1-based)")
    page_size: int = Field(
        default=50,
        ge=1,
        le=200,
        alias="page_size",
        description="Cantidad de registros por página",
    )
    offset: int = Field(
        default=0,
        ge=0,
        exclude=True,
        description="Offset calculado (no se usa directamente)",
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica."""

    data: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Formato estándar de error."""

    detail: str
    error_code: str = "INTERNAL_ERROR"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """Respuesta del endpoint de health check."""

    status: str
    version: str
    duckdb: str
    parquet_files: int
    total_records: int
