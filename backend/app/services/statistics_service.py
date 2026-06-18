"""StatisticsService — reglas de negocio para indicadores globales."""

import json

import duckdb

from app.core.config import settings
from app.repositories import statistics_repository
from app.schemas.stats import ModalitySummary, StatsResponse


def get_overview(conn: duckdb.DuckDBPyConnection) -> StatsResponse:
    """Obtiene indicadores globales de contratación.

    Args:
        conn: Conexión DuckDB.

    Returns:
        StatsResponse con KPIs principales.
    """
    total_contratos = statistics_repository.count_contracts(conn)
    total_entidades = statistics_repository.count_entities(conn)
    total_proveedores = statistics_repository.count_suppliers(conn)
    valor_contratado, valor_pagado = statistics_repository.total_values(conn)
    anio_desde, anio_hasta = statistics_repository.year_range(conn)

    ultima_actualizacion = _load_last_update()

    return StatsResponse(
        total_contratos=total_contratos,
        total_entidades=total_entidades,
        total_proveedores=total_proveedores,
        valor_total_contratado=valor_contratado,
        valor_total_pagado=valor_pagado,
        anio_desde=anio_desde,
        anio_hasta=anio_hasta,
        ultima_actualizacion=ultima_actualizacion,
    )


def list_modalities(conn: duckdb.DuckDBPyConnection) -> list[ModalitySummary]:
    """Lista modalidades de contratación con totales."""
    rows = statistics_repository.modalities(conn)
    return [ModalitySummary(**row) for row in rows]


def _load_last_update() -> str | None:
    """Carga la fecha de última actualización desde metadata ETL."""
    try:
        path = settings.etl_state_path
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            state = json.load(f)
        return state.get("last_watermark")
    except Exception:
        return None
