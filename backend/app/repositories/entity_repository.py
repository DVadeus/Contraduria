"""EntityRepository — consultas SQL agregadas por entidad."""

from typing import Any

import duckdb


def find_all(
    conn: duckdb.DuckDBPyConnection,
    search: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Lista entidades con totales agregados.

    Args:
        conn: Conexión DuckDB.
        search: Texto de búsqueda (nombre o NIT).
        offset: Offset.
        limit: Límite.

    Returns:
        Lista de diccionarios EntitySummary.
    """
    conditions = ["nit_entidad IS NOT NULL", "nombre_entidad IS NOT NULL"]
    params: dict[str, Any] = {}

    if search:
        conditions.append(
            "(nombre_entidad ILIKE '%' || $search || '%' OR nit_entidad = $search)"
        )
        params["search"] = search

    where = " AND ".join(conditions)
    sql = (
        "SELECT nit_entidad, MAX(nombre_entidad) AS nombre_entidad, "
        "COUNT(*) AS total_contratos, "
        "SUM(valor_contrato) AS valor_total, "
        "MAX(sector) AS sector "
        "FROM contratos "
        f"WHERE {where} "
        "GROUP BY nit_entidad "
        "ORDER BY valor_total DESC NULLS LAST "
        "LIMIT $limit_param OFFSET $offset_param"
    )
    params["limit_param"] = limit
    params["offset_param"] = offset

    result = conn.execute(sql, params)
    rows = result.fetchall()
    col_names = [desc[0] for desc in result.description]
    return [dict(zip(col_names, row)) for row in rows]


def count_all(conn: duckdb.DuckDBPyConnection, search: str | None = None) -> int:
    """Cuenta entidades únicas."""
    conditions = ["nit_entidad IS NOT NULL", "nombre_entidad IS NOT NULL"]
    params: dict[str, Any] = {}

    if search:
        conditions.append(
            "(nombre_entidad ILIKE '%' || $search || '%' OR nit_entidad = $search)"
        )
        params["search"] = search

    where = " AND ".join(conditions)
    sql = f"SELECT COUNT(DISTINCT nit_entidad) FROM contratos WHERE {where}"
    result = conn.execute(sql, params)
    row = result.fetchone()
    return row[0] if row else 0


def find_by_nit(conn: duckdb.DuckDBPyConnection, nit: str) -> dict[str, Any] | None:
    """Obtiene detalle de una entidad por NIT.

    Returns dict with: nit_entidad, nombre_entidad, total_contratos,
    valor_total, sector, departamento, ciudad.
    """
    sql = (
        "SELECT nit_entidad, MAX(nombre_entidad) AS nombre_entidad, "
        "COUNT(*) AS total_contratos, "
        "SUM(valor_contrato) AS valor_total, "
        "MAX(sector) AS sector, "
        "MAX(departamento) AS departamento, "
        "MAX(ciudad) AS ciudad "
        "FROM contratos WHERE nit_entidad = $nit GROUP BY nit_entidad"
    )
    result = conn.execute(sql, {"nit": nit})
    rows = result.fetchall()
    if not rows:
        return None
    col_names = [desc[0] for desc in result.description]
    return dict(zip(col_names, rows[0]))


def find_recent_contracts(
    conn: duckdb.DuckDBPyConnection, nit: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Obtiene contratos recientes de una entidad."""
    sql = (
        "SELECT id_contrato, nombre_entidad, proveedor_adjudicado, "
        "valor_contrato, fecha_firma, estado_contrato, modalidad_contratacion "
        "FROM contratos WHERE nit_entidad = $nit "
        "ORDER BY fecha_firma DESC NULLS LAST LIMIT $limit_param"
    )
    result = conn.execute(sql, {"nit": nit, "limit_param": limit})
    rows = result.fetchall()
    col_names = [desc[0] for desc in result.description]
    return [dict(zip(col_names, row)) for row in rows]
