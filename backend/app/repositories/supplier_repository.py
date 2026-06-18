"""SupplierRepository — consultas SQL agregadas por proveedor."""

from typing import Any

import duckdb


def find_all(
    conn: duckdb.DuckDBPyConnection,
    search: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Lista proveedores con totales agregados."""
    conditions = ["documento_proveedor IS NOT NULL", "proveedor_adjudicado IS NOT NULL"]
    params: dict[str, Any] = {}

    if search:
        conditions.append(
            "(proveedor_adjudicado ILIKE '%' || $search || '%' "
            "OR documento_proveedor = $search)"
        )
        params["search"] = search

    where = " AND ".join(conditions)
    sql = (
        "SELECT documento_proveedor, "
        "MAX(proveedor_adjudicado) AS proveedor_adjudicado, "
        "COUNT(*) AS total_contratos, "
        "SUM(valor_contrato) AS valor_total, "
        "MAX(es_pyme) AS es_pyme "
        "FROM contratos "
        f"WHERE {where} "
        "GROUP BY documento_proveedor "
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
    """Cuenta proveedores únicos."""
    conditions = ["documento_proveedor IS NOT NULL"]
    params: dict[str, Any] = {}

    if search:
        conditions.append(
            "(proveedor_adjudicado ILIKE '%' || $search || '%' "
            "OR documento_proveedor = $search)"
        )
        params["search"] = search

    where = " AND ".join(conditions)
    sql = f"SELECT COUNT(DISTINCT documento_proveedor) FROM contratos WHERE {where}"
    result = conn.execute(sql, params)
    row = result.fetchone()
    return row[0] if row else 0


def find_by_document(
    conn: duckdb.DuckDBPyConnection, doc: str
) -> dict[str, Any] | None:
    """Obtiene detalle de un proveedor por documento."""
    sql = (
        "SELECT documento_proveedor, "
        "MAX(proveedor_adjudicado) AS proveedor_adjudicado, "
        "COUNT(*) AS total_contratos, "
        "SUM(valor_contrato) AS valor_total, "
        "MAX(es_pyme) AS es_pyme "
        "FROM contratos WHERE documento_proveedor = $doc "
        "GROUP BY documento_proveedor"
    )
    result = conn.execute(sql, {"doc": doc})
    rows = result.fetchall()
    if not rows:
        return None
    col_names = [desc[0] for desc in result.description]
    return dict(zip(col_names, rows[0]))


def find_recent_contracts(
    conn: duckdb.DuckDBPyConnection, doc: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Obtiene contratos recientes de un proveedor."""
    sql = (
        "SELECT id_contrato, nombre_entidad, proveedor_adjudicado, "
        "valor_contrato, fecha_firma, estado_contrato, modalidad_contratacion "
        "FROM contratos WHERE documento_proveedor = $doc "
        "ORDER BY fecha_firma DESC NULLS LAST LIMIT $limit_param"
    )
    result = conn.execute(sql, {"doc": doc, "limit_param": limit})
    rows = result.fetchall()
    col_names = [desc[0] for desc in result.description]
    return [dict(zip(col_names, row)) for row in rows]
