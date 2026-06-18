"""DuckDB connection manager for Contraduria API.

Proporciona una conexión gestionada a DuckDB configurada para leer
los archivos Parquet desde el directorio Gold del proyecto.

Arquitectura:
- Conexión por request (no se usa pool — DuckDB es single-writer).
- Modo read_only por defecto.
- Registra la vista `contratos` sobre todos los contratos_*.parquet.
"""

import logging
from pathlib import Path

import duckdb

from app.core.config import settings

logger = logging.getLogger(__name__)


def create_connection(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    """Crea una conexión DuckDB configurada para el proyecto.

    Args:
        read_only: Si True (default), la conexión es de solo lectura.

    Returns:
        Conexión DuckDB lista para consultar.
    """
    parquet_dir = settings.parquet_dir_absolute
    parquet_files = sorted(parquet_dir.glob("contratos_*.parquet"))

    conn = duckdb.connect(database=":memory:", read_only=read_only)

    # Configurar threads y límite de memoria
    conn.execute(f"SET threads = {settings.duckdb_threads}")
    conn.execute(f"SET memory_limit = '{settings.duckdb_memory_limit}'")

    if parquet_files:
        # Registrar vista `contratos` unificando todos los archivos por año
        files_str = ", ".join(f"'{str(f)}'" for f in parquet_files)
        conn.execute(
            f"CREATE OR REPLACE VIEW contratos AS "
            f"SELECT * FROM read_parquet([{files_str}])"
        )
        logger.info(
            "Vista 'contratos' registrada desde %d archivos Parquet en %s",
            len(parquet_files),
            parquet_dir,
        )
    else:
        logger.warning(
            "No se encontraron archivos contratos_*.parquet en %s. "
            "La vista 'contratos' estará vacía.",
            parquet_dir,
        )

    return conn


def get_parquet_count(parquet_dir: Path | None = None) -> int:
    """Cuenta cuántos archivos contratos_*.parquet hay en el directorio Gold.

    Args:
        parquet_dir: Directorio opcional (default: settings.parquet_dir_absolute).

    Returns:
        Número de archivos Parquet encontrados.
    """
    target = parquet_dir or settings.parquet_dir_absolute
    return len(list(target.glob("contratos_*.parquet")))


def get_total_records(conn: duckdb.DuckDBPyConnection) -> int:
    """Obtiene el total de registros en la vista contratos.

    Args:
        conn: Conexión DuckDB activa.

    Returns:
        Número total de registros.
    """
    try:
        result = conn.execute("SELECT COUNT(*) FROM contratos").fetchone()
        return result[0] if result else 0
    except Exception:
        return 0
