"""Contracts router — endpoints REST para consulta de contratos."""

from datetime import date
from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_db
from app.schemas.common import ErrorResponse, PaginatedResponse
from app.schemas.contracts import ContractDetail
from app.services.contract_service import get_by_id, list_contracts

router = APIRouter(prefix="/contratos", tags=["Contratos"])


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="Listar contratos",
    description="Obtiene una lista paginada de contratos con filtros opcionales.",
    responses={503: {"model": ErrorResponse, "description": "Datos no disponibles"}},
)
def get_contracts(
    conn: duckdb.DuckDBPyConnection = Depends(get_db),
    anio: Optional[int] = Query(None, ge=2000, le=2100, description="Año de firma"),
    entidad: Optional[str] = Query(None, description="Nombre o NIT de entidad"),
    proveedor: Optional[str] = Query(
        None, description="Nombre o documento de proveedor"
    ),
    modalidad: Optional[str] = Query(None, description="Modalidad de contratación"),
    fecha_desde: Optional[date] = Query(
        None, description="Fecha de firma desde (YYYY-MM-DD)"
    ),
    fecha_hasta: Optional[date] = Query(
        None, description="Fecha de firma hasta (YYYY-MM-DD)"
    ),
    valor_min: Optional[float] = Query(
        None, ge=0, description="Valor mínimo del contrato"
    ),
    valor_max: Optional[float] = Query(
        None, ge=0, description="Valor máximo del contrato"
    ),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=1, le=200, description="Registros por página"),
):
    """Lista contratos con filtros y paginación."""
    filters = {
        "anio": anio,
        "entidad": entidad,
        "proveedor": proveedor,
        "modalidad": modalidad,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "valor_min": valor_min,
        "valor_max": valor_max,
    }
    return list_contracts(conn, filters, page=page, page_size=page_size)


@router.get(
    "/{id_contrato}",
    response_model=ContractDetail,
    summary="Obtener contrato por ID",
    description="Busca un contrato por su identificador único.",
    responses={
        404: {"model": ErrorResponse, "description": "Contrato no encontrado"},
    },
)
def get_contract(
    id_contrato: str,
    conn: duckdb.DuckDBPyConnection = Depends(get_db),
):
    """Obtiene un contrato por su ID."""
    return get_by_id(conn, id_contrato)
