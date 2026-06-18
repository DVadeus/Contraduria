"""Modalities router — endpoint REST para consulta de modalidades de contratación."""

import duckdb
from fastapi import APIRouter, Depends

from app.api.dependencies import get_db
from app.schemas.stats import ModalitySummary
from app.services.statistics_service import list_modalities

router = APIRouter(prefix="/modalidades", tags=["Modalidades"])


@router.get(
    "",
    response_model=list[ModalitySummary],
    summary="Listar modalidades de contratación",
    description="Obtiene la distribución de contratos por modalidad de contratación.",
)
def get_modalities(
    conn: duckdb.DuckDBPyConnection = Depends(get_db),
):
    """Lista modalidades con totales agregados."""
    return list_modalities(conn)
