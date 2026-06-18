"""EntityService — reglas de negocio para entidades."""

import math

import duckdb

from app.core.exceptions import NotFoundError
from app.repositories import entity_repository
from app.schemas.common import PaginatedResponse
from app.schemas.entities import EntityDetail, EntitySummary


def list_entities(
    conn: duckdb.DuckDBPyConnection,
    search: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> PaginatedResponse[EntitySummary]:
    """Lista entidades con búsqueda y paginación."""
    offset = (page - 1) * page_size
    rows = entity_repository.find_all(
        conn, search=search, offset=offset, limit=page_size
    )
    total = entity_repository.count_all(conn, search=search)
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    summaries = [EntitySummary(**row) for row in rows]
    return PaginatedResponse(
        data=summaries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def get_by_nit(conn: duckdb.DuckDBPyConnection, nit: str) -> EntityDetail:
    """Obtiene detalle de entidad por NIT."""
    row = entity_repository.find_by_nit(conn, nit)
    if row is None:
        raise NotFoundError(f"Entidad con NIT '{nit}' no encontrada")
    return EntityDetail(**row)
