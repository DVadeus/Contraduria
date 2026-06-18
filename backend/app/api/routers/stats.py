"""Stats router — endpoint REST para indicadores globales."""

import duckdb
from fastapi import APIRouter, Depends

from app.api.dependencies import get_db
from app.schemas.stats import StatsResponse
from app.services.statistics_service import get_overview

router = APIRouter(prefix="/stats", tags=["Estadísticas"])


@router.get(
    "",
    response_model=StatsResponse,
    summary="Indicadores globales",
    description="Obtiene los KPIs principales de contratación pública.",
)
def get_stats(
    conn: duckdb.DuckDBPyConnection = Depends(get_db),
):
    """Obtiene indicadores globales de contratación."""
    return get_overview(conn)
