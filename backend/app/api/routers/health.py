"""Health check endpoint."""

import duckdb
from fastapi import APIRouter, Depends

from app.api.dependencies import get_db
from app.core.config import settings
from app.db.database import get_parquet_count, get_total_records

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health check",
    description="Verifica que la API esté operativa y que DuckDB pueda consultar los datos.",
)
def health_check(conn: duckdb.DuckDBPyConnection = Depends(get_db)):
    """Endpoint de health check con estado de la API y DuckDB."""
    duckdb_status = "ok"
    try:
        conn.execute("SELECT 1 FROM contratos LIMIT 1")
    except Exception:
        duckdb_status = "error — vista contratos no disponible"

    return {
        "status": "ok",
        "version": settings.app_version,
        "duckdb": duckdb_status,
        "parquet_files": get_parquet_count(),
        "total_records": get_total_records(conn),
    }
