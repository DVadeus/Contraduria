"""Entities router — endpoints REST para consulta de entidades."""

from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_db
from app.schemas.common import ErrorResponse, PaginatedResponse
from app.schemas.entities import EntityDetail
from app.services.entity_service import get_by_nit, list_entities

router = APIRouter(prefix="/entidades", tags=["Entidades"])


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="Listar entidades",
    description="Obtiene una lista paginada de entidades contratantes.",
)
def get_entities(
    conn: duckdb.DuckDBPyConnection = Depends(get_db),
    search: Optional[str] = Query(None, description="Buscar por nombre o NIT"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=1, le=200, description="Registros por página"),
):
    """Lista entidades con búsqueda opcional."""
    return list_entities(conn, search=search, page=page, page_size=page_size)


@router.get(
    "/{nit}",
    response_model=EntityDetail,
    summary="Obtener entidad por NIT",
    description="Busca una entidad por su NIT y retorna detalle con agregados.",
    responses={404: {"model": ErrorResponse, "description": "Entidad no encontrada"}},
)
def get_entity(
    nit: str,
    conn: duckdb.DuckDBPyConnection = Depends(get_db),
):
    """Obtiene detalle de entidad por NIT."""
    return get_by_nit(conn, nit)
