"""Suppliers router — endpoints REST para consulta de proveedores."""

from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_db
from app.schemas.common import ErrorResponse, PaginatedResponse
from app.schemas.suppliers import SupplierDetail
from app.services.supplier_service import get_by_document, list_suppliers

router = APIRouter(prefix="/proveedores", tags=["Proveedores"])


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="Listar proveedores",
    description="Obtiene una lista paginada de proveedores.",
)
def get_suppliers(
    conn: duckdb.DuckDBPyConnection = Depends(get_db),
    search: Optional[str] = Query(None, description="Buscar por nombre o documento"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=1, le=200, description="Registros por página"),
):
    """Lista proveedores con búsqueda opcional."""
    return list_suppliers(conn, search=search, page=page, page_size=page_size)


@router.get(
    "/{documento}",
    response_model=SupplierDetail,
    summary="Obtener proveedor por documento",
    description="Busca un proveedor por su número de documento.",
    responses={404: {"model": ErrorResponse, "description": "Proveedor no encontrado"}},
)
def get_supplier(
    documento: str,
    conn: duckdb.DuckDBPyConnection = Depends(get_db),
):
    """Obtiene detalle de proveedor por documento."""
    return get_by_document(conn, documento)
