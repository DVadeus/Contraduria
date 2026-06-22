"""Repositorio analítico — consultas agregadas sobre DuckDB + Parquet.

Responsable ÚNICAMENTE de ejecutar consultas analíticas y devolver
datos estructurados. No contiene reglas de negocio.
"""

from decimal import Decimal
from typing import Any

import duckdb


def get_top_contractors(
    conn: duckdb.DuckDBPyConnection,
    parquet_glob: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Obtiene el ranking de contratistas por valor total adjudicado.

    Args:
        conn: Conexión DuckDB.
        parquet_glob: Patrón glob para archivos Parquet.
        limit: Número máximo de contratistas a retornar.

    Returns:
        Lista de diccionarios con contratista, total_contratos, valor_total, valor_promedio.
    """
    query = f"""
        SELECT
            proveedor_adjudicado AS contratista,
            COUNT(*) AS total_contratos,
            SUM(valor_contrato) AS valor_total,
            AVG(valor_contrato) AS valor_promedio
        FROM '{parquet_glob}'
        GROUP BY proveedor_adjudicado
        ORDER BY valor_total DESC
        LIMIT ?
    """
    result = conn.execute(query, [limit]).fetchdf()
    return [
        {
            "contratista": row["contratista"],
            "total_contratos": int(row["total_contratos"]),
            "valor_total": Decimal(str(row["valor_total"]))
            if row["valor_total"] is not None
            else Decimal("0"),
            "valor_promedio": Decimal(str(row["valor_promedio"]))
            if row["valor_promedio"] is not None
            else Decimal("0"),
        }
        for _, row in result.iterrows()
    ]


def count_unique_contractors(
    conn: duckdb.DuckDBPyConnection,
    parquet_glob: str,
) -> int:
    """Cuenta el número de contratistas únicos.

    Args:
        conn: Conexión DuckDB.
        parquet_glob: Patrón glob para archivos Parquet.

    Returns:
        Número de contratistas únicos.
    """
    query = f"""
        SELECT COUNT(DISTINCT proveedor_adjudicado) AS total
        FROM '{parquet_glob}'
    """
    result = conn.execute(query).fetchone()
    return result[0] if result else 0


def get_by_locality(
    conn: duckdb.DuckDBPyConnection,
    parquet_glob: str,
) -> list[dict[str, Any]]:
    """Obtiene agregados de contratación por localidad.

    Args:
        conn: Conexión DuckDB.
        parquet_glob: Patrón glob para archivos Parquet.

    Returns:
        Lista de diccionarios con localidad, total_contratos, valor_total,
        contratistas_unicos, entidades_unicas.
    """
    query = f"""
        SELECT
            localizacion AS localidad,
            COUNT(*) AS total_contratos,
            SUM(valor_contrato) AS valor_total,
            COUNT(DISTINCT proveedor_adjudicado) AS contratistas_unicos,
            COUNT(DISTINCT nombre_entidad) AS entidades_unicas
        FROM '{parquet_glob}'
        WHERE localizacion IS NOT NULL
        GROUP BY localizacion
        ORDER BY valor_total DESC
    """
    result = conn.execute(query).fetchdf()
    return [
        {
            "localidad": row["localidad"],
            "total_contratos": int(row["total_contratos"]),
            "valor_total": Decimal(str(row["valor_total"]))
            if row["valor_total"] is not None
            else Decimal("0"),
            "contratistas_unicos": int(row["contratistas_unicos"]),
            "entidades_unicas": int(row["entidades_unicas"]),
        }
        for _, row in result.iterrows()
    ]


def get_risk_contracts(
    conn: duckdb.DuckDBPyConnection,
    parquet_glob: str,
    threshold_contractor: int = 10,
    outlier_multiplier: int = 5,
) -> list[dict[str, Any]]:
    """Identifica contratos con posibles riesgos de contratación.

    Indicadores:
    1. Contratista con alta concentración (> threshold_contractor contratos).
    2. Valor del contrato atípicamente alto frente al promedio del contratista.

    Args:
        conn: Conexión DuckDB.
        parquet_glob: Patrón glob para archivos Parquet.
        threshold_contractor: Umbral de contratos para marcar concentración.
        outlier_multiplier: Multiplicador del promedio para detectar valores atípicos.

    Returns:
        Lista de contratos con indicadores de riesgo.
    """
    query = f"""
        WITH contractor_stats AS (
            SELECT
                proveedor_adjudicado,
                COUNT(*) AS total_contratos_contratista,
                AVG(valor_contrato) AS valor_promedio_contratista
            FROM '{parquet_glob}'
            GROUP BY proveedor_adjudicado
        )
        SELECT
            c.proceso_de_compra,
            c.proveedor_adjudicado,
            c.nombre_entidad,
            c.valor_contrato,
            cs.total_contratos_contratista,
            cs.valor_promedio_contratista
        FROM '{parquet_glob}' c
        JOIN contractor_stats cs
            ON c.proveedor_adjudicado = cs.proveedor_adjudicado
        WHERE
            cs.total_contratos_contratista > ?
            OR c.valor_contrato > cs.valor_promedio_contratista * ?
        ORDER BY c.valor_contrato DESC
    """
    result = conn.execute(query, [threshold_contractor, outlier_multiplier]).fetchdf()

    contracts = []
    for _, row in result.iterrows():
        indicadores = []
        nivel = "bajo"

        if row["total_contratos_contratista"] > threshold_contractor:
            indicadores.append(
                f"Alta concentración: {int(row['total_contratos_contratista'])} contratos"
            )

        avg_val = row["valor_promedio_contratista"]
        if (
            avg_val
            and row["valor_contrato"]
            and row["valor_contrato"] > avg_val * outlier_multiplier
        ):
            indicadores.append("Valor atípico frente al promedio del contratista")

        # Clasificar nivel de riesgo
        if len(indicadores) >= 2:
            nivel = "alto"
        elif len(indicadores) == 1:
            nivel = "medio"

        contracts.append(
            {
                "proceso_id": row["proceso_de_compra"],
                "contratista": row["proveedor_adjudicado"],
                "entidad": row["nombre_entidad"],
                "valor_contrato": Decimal(str(row["valor_contrato"]))
                if row["valor_contrato"] is not None
                else Decimal("0"),
                "nivel_riesgo": nivel,
                "indicadores": indicadores,
            }
        )

    return contracts


def get_kpi(
    conn: duckdb.DuckDBPyConnection,
    parquet_glob: str,
) -> dict[str, Any]:
    """Calcula los KPIs principales del dashboard.

    Args:
        conn: Conexión DuckDB.
        parquet_glob: Patrón glob para archivos Parquet.

    Returns:
        Diccionario con total_contratos, valor_total, valor_promedio,
        contratistas_unicos, entidades_unicas, localidades_cubiertas.
    """
    query = f"""
        SELECT
            COUNT(*) AS total_contratos,
            SUM(valor_contrato) AS valor_total,
            AVG(valor_contrato) AS valor_promedio,
            COUNT(DISTINCT proveedor_adjudicado) AS contratistas_unicos,
            COUNT(DISTINCT nombre_entidad) AS entidades_unicas,
            COUNT(DISTINCT localizacion) AS localidades_cubiertas
        FROM '{parquet_glob}'
    """
    result = conn.execute(query).fetchone()
    return {
        "total_contratos": result[0] if result else 0,
        "valor_total": Decimal(str(result[1])) if result[1] else Decimal("0"),
        "valor_promedio": Decimal(str(result[2])) if result[2] else Decimal("0"),
        "contratistas_unicos": result[3] if result else 0,
        "entidades_unicas": result[4] if result else 0,
        "localidades_cubiertas": result[5] if result else 0,
    }
