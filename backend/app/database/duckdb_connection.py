"""Módulo de conexión a DuckDB — motor analítico oficial del proyecto.

Proporciona una conexión gestionada a DuckDB que consulta directamente
los archivos Parquet del directorio data/parquet/.
"""

import os
from pathlib import Path

import duckdb

# Directorio raíz del proyecto (2 niveles arriba desde database/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_PARQUET_DIR = _PROJECT_ROOT / "data" / "parquet"


def _resolve_parquet_dir() -> str:
    """Resuelve el directorio de Parquet, permitiendo override por variable de entorno."""
    env_dir = os.getenv("CONTRADURIA_PARQUET_DIR")
    if env_dir:
        return env_dir
    return str(_PARQUET_DIR)


def get_connection(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    """Devuelve una conexión DuckDB lista para consultar los Parquet del proyecto.

    Args:
        read_only: Si True, la conexión es de solo lectura (por defecto).

    Returns:
        Conexión DuckDB configurada.
    """
    conn = duckdb.connect(database=":memory:", read_only=read_only)
    parquet_dir = _resolve_parquet_dir()
    conn.execute(f"SET search_path = '{parquet_dir}'")
    return conn
