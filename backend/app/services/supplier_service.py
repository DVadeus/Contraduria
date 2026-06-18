"""SupplierService — reglas de negocio para proveedores."""

import math

import duckdb

from app.core.exceptions import NotFoundError
from app.repositories import supplier_repository
from app.schemas.common import PaginatedResponse
from app.schemas.suppliers import SupplierDetail, SupplierSummary


def list_suppliers(
    conn: duckdb.DuckDBPyConnection,
    search: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> PaginatedResponse[SupplierSummary]:
    """Lista proveedores con búsqueda y paginación."""
    offset = (page - 1) * page_size
    rows = supplier_repository.find_all(
        conn, search=search, offset=offset, limit=page_size
    )
    total = supplier_repository.count_all(conn, search=search)
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    summaries = [SupplierSummary(**row) for row in rows]
    return PaginatedResponse(
        data=summaries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def get_by_document(conn: duckdb.DuckDBPyConnection, doc: str) -> SupplierDetail:
    """Obtiene detalle de proveedor por documento."""
    row = supplier_repository.find_by_document(conn, doc)
    if row is None:
        raise NotFoundError(f"Proveedor con documento '{doc}' no encontrado")
    return SupplierDetail(**row)
