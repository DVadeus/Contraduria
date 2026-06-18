"""StatisticsRepository — consultas SQL para indicadores globales."""

from typing import Any

import duckdb


def count_contracts(conn: duckdb.DuckDBPyConnection) -> int:
    """Total de contratos."""
    result = conn.execute("SELECT COUNT(*) FROM contratos")
    row = result.fetchone()
    return row[0] if row else 0


def count_entities(conn: duckdb.DuckDBPyConnection) -> int:
    """Total de entidades únicas."""
    result = conn.execute(
        "SELECT COUNT(DISTINCT nit_entidad) FROM contratos WHERE nit_entidad IS NOT NULL"
    )
    row = result.fetchone()
    return row[0] if row else 0


def count_suppliers(conn: duckdb.DuckDBPyConnection) -> int:
    """Total de proveedores únicos."""
    result = conn.execute(
        "SELECT COUNT(DISTINCT documento_proveedor) FROM contratos "
        "WHERE documento_proveedor IS NOT NULL"
    )
    row = result.fetchone()
    return row[0] if row else 0


def total_values(conn: duckdb.DuckDBPyConnection) -> tuple[float, float]:
    """Suma total de valor contratado y pagado."""
    result = conn.execute(
        "SELECT COALESCE(SUM(valor_contrato), 0), COALESCE(SUM(valor_pagado), 0) "
        "FROM contratos"
    )
    row = result.fetchone()
    if row:
        return float(row[0] or 0), float(row[1] or 0)
    return 0.0, 0.0


def year_range(conn: duckdb.DuckDBPyConnection) -> tuple[int, int]:
    """Rango de años del dataset."""
    result = conn.execute(
        "SELECT COALESCE(MIN(YEAR(fecha_firma)), 0), "
        "COALESCE(MAX(YEAR(fecha_firma)), 0) "
        "FROM contratos WHERE fecha_firma IS NOT NULL"
    )
    row = result.fetchone()
    if row:
        return int(row[0] or 0), int(row[1] or 0)
    return 0, 0


def modalities(conn: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Distribución por modalidad de contratación."""
    sql = (
        "SELECT modalidad_contratacion AS modalidad, "
        "COUNT(*) AS total_contratos, "
        "SUM(valor_contrato) AS valor_total "
        "FROM contratos "
        "WHERE modalidad_contratacion IS NOT NULL "
        "GROUP BY modalidad_contratacion "
        "ORDER BY COUNT(*) DESC"
    )
    result = conn.execute(sql)
    rows = result.fetchall()
    col_names = [desc[0] for desc in result.description]
    return [dict(zip(col_names, row)) for row in rows]
