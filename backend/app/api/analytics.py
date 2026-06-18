"""Router de analytics — endpoints REST para indicadores y análisis.

Responsable ÚNICAMENTE de:
- Recibir requests HTTP.
- Validar parámetros de entrada.
- Invocar servicios.
- Devolver respuestas HTTP.

No contiene lógica de negocio ni acceso a datos.
"""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.database.duckdb_connection import get_connection
from app.schemas.analytics import (
    KPIResponse,
    LocalityResponse,
    RiskResponse,
    TopContractorsResponse,
)
from app.schemas.contracts import ErrorResponse
from app.services.analytics_service import (
    compute_by_locality,
    compute_kpi,
    compute_risk_contracts,
    compute_top_contractors,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Directorio de datos — configurable vía variable de entorno
_DATA_DIR = os.getenv(
    "CONTRADURIA_DATA_DIR",
    str(Path(__file__).resolve().parent.parent.parent.parent.parent / "data"),
)


@router.get(
    "/kpi",
    response_model=KPIResponse,
    summary="KPIs principales",
    description="Obtiene los indicadores clave del dashboard: total contratos, valor total, promedio, contratistas únicos, entidades, localidades.",
    responses={
        200: {"description": "KPIs calculados"},
        503: {"model": ErrorResponse, "description": "Datos no disponibles"},
    },
)
def get_kpi():
    """Obtiene KPIs principales del dashboard."""
    try:
        conn = get_connection()
        result = compute_kpi(conn, _DATA_DIR)
        conn.close()
        return result
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get(
    "/top-contractors",
    response_model=TopContractorsResponse,
    summary="Top contratistas",
    description="Ranking de contratistas por valor total adjudicado.",
    responses={
        200: {"description": "Ranking de contratistas"},
        503: {"model": ErrorResponse, "description": "Datos no disponibles"},
    },
)
def get_top_contractors(
    limit: int = Query(
        20, ge=1, le=100, description="Número máximo de contratistas a retornar"
    ),
):
    """Obtiene ranking de contratistas por valor total."""
    try:
        conn = get_connection()
        result = compute_top_contractors(conn, _DATA_DIR, limit=limit)
        conn.close()
        return result
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get(
    "/by-locality",
    response_model=LocalityResponse,
    summary="Contratación por localidad",
    description="Métricas agregadas de contratación por localidad: contratos, valor, contratistas y entidades únicas.",
    responses={
        200: {"description": "Datos por localidad"},
        503: {"model": ErrorResponse, "description": "Datos no disponibles"},
    },
)
def get_by_locality():
    """Obtiene métricas de contratación por localidad."""
    try:
        conn = get_connection()
        result = compute_by_locality(conn, _DATA_DIR)
        conn.close()
        return result
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get(
    "/risk-contracts",
    response_model=RiskResponse,
    summary="Contratos con riesgos",
    description="Identifica contratos con posibles riesgos de contratación: alta concentración de contratistas y valores atípicos.",
    responses={
        200: {"description": "Contratos con indicadores de riesgo"},
        503: {"model": ErrorResponse, "description": "Datos no disponibles"},
    },
)
def get_risk_contracts(
    threshold_contractor: int = Query(
        10, ge=1, le=100, description="Umbral de contratos para marcar concentración"
    ),
    outlier_multiplier: int = Query(
        5,
        ge=2,
        le=20,
        description="Multiplicador del promedio para detectar valores atípicos",
    ),
):
    """Identifica contratos con posibles riesgos."""
    try:
        conn = get_connection()
        result = compute_risk_contracts(
            conn,
            _DATA_DIR,
            threshold_contractor=threshold_contractor,
            outlier_multiplier=outlier_multiplier,
        )
        conn.close()
        return result
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
