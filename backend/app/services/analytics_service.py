"""Servicio de analytics — lógica de negocio para indicadores y análisis.

Contiene reglas de negocio, agregaciones y cálculos de riesgo.
No accede a DuckDB directamente; usa el repositorio.
"""

from pathlib import Path

import duckdb

from app.repositories.analytics_repository import (
    count_unique_contractors,
    get_by_locality,
    get_kpi,
    get_risk_contracts,
    get_top_contractors,
)
from app.schemas.analytics import (
    KPIResponse,
    LocalityItem,
    LocalityResponse,
    RiskContractItem,
    RiskResponse,
    TopContractorsItem,
    TopContractorsResponse,
)


def _get_parquet_glob(data_dir: str) -> str:
    """Devuelve el patrón glob para consultar todos los años."""
    parquet_dir = Path(data_dir) / "parquet"
    return str(parquet_dir / "contratos_*.parquet")


def _validate_data_exists(data_dir: str) -> None:
    """Valida que existan archivos Parquet en el directorio de datos.

    Args:
        data_dir: Directorio base de datos del proyecto.

    Raises:
        ValueError: Si no hay archivos Parquet disponibles.
    """
    parquet_dir = Path(data_dir) / "parquet"
    if not parquet_dir.exists() or not list(parquet_dir.glob("contratos_*.parquet")):
        raise ValueError("No hay archivos Parquet disponibles. Ejecute el ETL primero.")


def compute_top_contractors(
    conn: duckdb.DuckDBPyConnection,
    data_dir: str,
    limit: int = 20,
) -> TopContractorsResponse:
    """Calcula el ranking de contratistas por valor total.

    Args:
        conn: Conexión DuckDB.
        data_dir: Directorio base de datos del proyecto.
        limit: Número máximo de contratistas a retornar.

    Returns:
        TopContractorsResponse con ranking y total de contratistas.

    Raises:
        ValueError: Si no hay datos disponibles.
    """
    _validate_data_exists(data_dir)
    parquet_glob = _get_parquet_glob(data_dir)

    items_data = get_top_contractors(conn, parquet_glob, limit=limit)
    total = count_unique_contractors(conn, parquet_glob)

    items = [
        TopContractorsItem(
            contratista=item["contratista"],
            total_contratos=item["total_contratos"],
            valor_total=item["valor_total"],
            valor_promedio=item["valor_promedio"],
        )
        for item in items_data
    ]

    return TopContractorsResponse(
        data=items,
        total_contratistas=total,
    )


def compute_by_locality(
    conn: duckdb.DuckDBPyConnection,
    data_dir: str,
) -> LocalityResponse:
    """Calcula métricas agregadas por localidad.

    Args:
        conn: Conexión DuckDB.
        data_dir: Directorio base de datos del proyecto.

    Returns:
        LocalityResponse con datos por localidad.

    Raises:
        ValueError: Si no hay datos disponibles.
    """
    _validate_data_exists(data_dir)
    parquet_glob = _get_parquet_glob(data_dir)

    items_data = get_by_locality(conn, parquet_glob)

    items = [
        LocalityItem(
            localidad=item["localidad"],
            total_contratos=item["total_contratos"],
            valor_total=item["valor_total"],
            contratistas_unicos=item["contratistas_unicos"],
            entidades_unicas=item["entidades_unicas"],
        )
        for item in items_data
    ]

    return LocalityResponse(
        data=items,
        total_localidades=len(items_data),
    )


def compute_risk_contracts(
    conn: duckdb.DuckDBPyConnection,
    data_dir: str,
    threshold_contractor: int = 10,
    outlier_multiplier: int = 5,
) -> RiskResponse:
    """Identifica contratos con posibles riesgos contractuales.

    Args:
        conn: Conexión DuckDB.
        data_dir: Directorio base de datos del proyecto.
        threshold_contractor: Umbral de contratos para marcar concentración.
        outlier_multiplier: Multiplicador del promedio para detectar valores atípicos.

    Returns:
        RiskResponse con contratos marcados y nivel de riesgo.

    Raises:
        ValueError: Si no hay datos disponibles.
    """
    _validate_data_exists(data_dir)
    parquet_glob = _get_parquet_glob(data_dir)

    risk_data = get_risk_contracts(
        conn,
        parquet_glob,
        threshold_contractor=threshold_contractor,
        outlier_multiplier=outlier_multiplier,
    )

    items = [
        RiskContractItem(
            proceso_id=item["proceso_id"],
            contratista=item["contratista"],
            entidad=item["entidad"],
            valor_contrato=item["valor_contrato"],
            nivel_riesgo=item["nivel_riesgo"],
            indicadores=item["indicadores"],
        )
        for item in risk_data
    ]

    return RiskResponse(
        data=items,
        total_analizados=len(risk_data),
    )


def compute_kpi(
    conn: duckdb.DuckDBPyConnection,
    data_dir: str,
) -> KPIResponse:
    """Calcula los KPIs principales del dashboard.

    Args:
        conn: Conexión DuckDB.
        data_dir: Directorio base de datos del proyecto.

    Returns:
        KPIResponse con indicadores clave.

    Raises:
        ValueError: Si no hay datos disponibles.
    """
    _validate_data_exists(data_dir)
    parquet_glob = _get_parquet_glob(data_dir)

    kpi_data = get_kpi(conn, parquet_glob)

    return KPIResponse(
        total_contratos=kpi_data["total_contratos"],
        valor_total=kpi_data["valor_total"],
        valor_promedio=kpi_data["valor_promedio"],
        contratistas_unicos=kpi_data["contratistas_unicos"],
        entidades_unicas=kpi_data["entidades_unicas"],
        localidades_cubiertas=kpi_data["localidades_cubiertas"],
    )
