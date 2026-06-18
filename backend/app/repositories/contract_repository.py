"""ContractRepository — consultas SQL parametrizadas sobre la vista `contratos`.

Responsabilidades:
- Buscar contratos con filtros dinámicos.
- Contar total matching registros.
- Obtener contrato por ID.
"""

from typing import Any

import duckdb

_SUMMARY_COLUMNS = [
    "id_contrato",
    "nombre_entidad",
    "proveedor_adjudicado",
    "valor_contrato",
    "fecha_firma",
    "estado_contrato",
    "modalidad_contratacion",
]

_DETAIL_COLUMNS = _SUMMARY_COLUMNS + [
    "nit_entidad",
    "departamento",
    "ciudad",
    "objeto_contrato",
    "fecha_inicio",
    "fecha_fin",
    "valor_pagado",
    "valor_facturado",
    "documento_proveedor",
    "url_proceso",
    "tipo_contrato",
    "duracion_contrato",
    "dias_adicionados",
    "localizacion",
    "sector",
    "rama",
    "origen_recursos",
    "destino_gasto",
    "es_postconflicto",
]


def _build_where_clause(filters: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Construye WHERE dinámico con parámetros nombrados.

    Args:
        filters: Diccionario de filtros (anio, entidad, proveedor, modalidad, etc.)

    Returns:
        Tupla (cláusula SQL, params dict).
    """
    conditions: list[str] = []
    params: dict[str, Any] = {}

    if filters.get("anio"):
        conditions.append("YEAR(fecha_firma) = $anio")
        params["anio"] = filters["anio"]

    if filters.get("entidad"):
        ent = filters["entidad"]
        conditions.append(
            "(nombre_entidad ILIKE '%' || $entidad || '%' OR nit_entidad = $entidad)"
        )
        params["entidad"] = ent

    if filters.get("proveedor"):
        prov = filters["proveedor"]
        conditions.append(
            "(proveedor_adjudicado ILIKE '%' || $proveedor || '%' "
            "OR documento_proveedor = $proveedor)"
        )
        params["proveedor"] = prov

    if filters.get("modalidad"):
        conditions.append("modalidad_contratacion = $modalidad")
        params["modalidad"] = filters["modalidad"]

    if filters.get("fecha_desde"):
        conditions.append("fecha_firma >= $fecha_desde")
        params["fecha_desde"] = filters["fecha_desde"]

    if filters.get("fecha_hasta"):
        conditions.append("fecha_firma <= $fecha_hasta")
        params["fecha_hasta"] = filters["fecha_hasta"]

    if filters.get("valor_min"):
        conditions.append("valor_contrato >= $valor_min")
        params["valor_min"] = filters["valor_min"]

    if filters.get("valor_max"):
        conditions.append("valor_contrato <= $valor_max")
        params["valor_max"] = filters["valor_max"]

    where = " AND ".join(conditions) if conditions else "1 = 1"
    return where, params


def find_all(
    conn: duckdb.DuckDBPyConnection,
    filters: dict[str, Any],
    offset: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Busca contratos con filtros y paginación.

    Args:
        conn: Conexión DuckDB.
        filters: Diccionario de filtros.
        offset: Offset para paginación.
        limit: Límite de registros.

    Returns:
        Lista de diccionarios con los campos de ContractSummary.
    """
    where_clause, params = _build_where_clause(filters)
    columns = ", ".join(_SUMMARY_COLUMNS)
    sql = (
        f"SELECT {columns} FROM contratos "
        f"WHERE {where_clause} "
        f"ORDER BY fecha_firma DESC NULLS LAST "
        f"LIMIT $limit_param OFFSET $offset_param"
    )
    params["limit_param"] = limit
    params["offset_param"] = offset

    result = conn.execute(sql, params)
    rows = result.fetchall()
    col_names = [desc[0] for desc in result.description]
    return [dict(zip(col_names, row)) for row in rows]


def count_all(conn: duckdb.DuckDBPyConnection, filters: dict[str, Any]) -> int:
    """Cuenta el total de contratos que coinciden con los filtros.

    Args:
        conn: Conexión DuckDB.
        filters: Diccionario de filtros.

    Returns:
        Número total de contratos.
    """
    where_clause, params = _build_where_clause(filters)
    sql = f"SELECT COUNT(*) FROM contratos WHERE {where_clause}"
    result = conn.execute(sql, params)
    row = result.fetchone()
    return row[0] if row else 0


def find_by_id(
    conn: duckdb.DuckDBPyConnection, id_contrato: str
) -> dict[str, Any] | None:
    """Busca un contrato por su ID.

    Args:
        conn: Conexión DuckDB.
        id_contrato: Identificador del contrato.

    Returns:
        Diccionario con los campos de ContractDetail, o None si no existe.
    """
    columns = ", ".join(_DETAIL_COLUMNS)
    sql = f"SELECT {columns} FROM contratos WHERE id_contrato = $id"
    result = conn.execute(sql, {"id": id_contrato})
    rows = result.fetchall()
    if not rows:
        return None
    col_names = [desc[0] for desc in result.description]
    return dict(zip(col_names, rows[0]))


def find_years(conn: duckdb.DuckDBPyConnection) -> list[int]:
    """Obtiene los años disponibles en el dataset.

    Args:
        conn: Conexión DuckDB.

    Returns:
        Lista de años ordenados.
    """
    sql = "SELECT DISTINCT YEAR(fecha_firma) AS anio FROM contratos WHERE fecha_firma IS NOT NULL ORDER BY anio"
    result = conn.execute(sql)
    return [row[0] for row in result.fetchall()]
