"""Loader Gold — particiona datos Silver en Parquet por año y registra en DuckDB.

Soporta carga FULL (primera ejecución) e INCREMENTAL (upsert por año sobre
archivos Parquet existentes).

Reglas ETL aplicadas:
- Particionado únicamente por año.
- Formato Parquet como almacenamiento principal.
- DuckDB como motor analítico.
- Incremental: solo actualiza años afectados.
- Validación de integridad post-carga.
"""

import logging
from pathlib import Path
from typing import Optional

import duckdb
import polars as pl

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración por defecto
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"
_PARQUET_DIR = _PROJECT_ROOT / "data" / "parquet"

SILVER_FILE = "contratos_silver.parquet"
GOLD_PATTERN = "contratos_{year}.parquet"

PRIMARY_KEY = "id_contrato"


def _read_silver(silver_path: Path) -> pl.DataFrame:
    """Lee el archivo Silver unificado."""
    if not silver_path.exists():
        raise FileNotFoundError(
            f"Archivo Silver no encontrado: {silver_path}. "
            "Ejecute primero la transformación con transform_raw_files()."
        )

    df = pl.read_parquet(silver_path)
    logger.info(
        "Silver cargado: %d registros, %d columnas desde %s",
        len(df),
        len(df.columns),
        silver_path,
    )
    return df


def _validate_silver(df: pl.DataFrame) -> None:
    """Valida la integridad básica del dataset Silver antes de cargar a Gold."""
    if len(df) == 0:
        raise ValueError("El dataset Silver está vacío. No hay datos para cargar.")

    if "anio" not in df.columns:
        raise ValueError(
            "Columna 'anio' no encontrada en el dataset Silver. "
            "La transformación debe generarla desde fecha_firma."
        )

    if PRIMARY_KEY not in df.columns:
        logger.warning(
            "Columna '%s' no encontrada. No se podrá validar unicidad.", PRIMARY_KEY
        )

    year_dist = df.group_by("anio").agg(pl.len().alias("cantidad")).sort("anio")
    logger.info("Distribución de registros por año:")
    for row in year_dist.iter_rows(named=True):
        logger.info("  Año %s: %d registros", row["anio"], row["cantidad"])


def _partition_by_year_full(df: pl.DataFrame, parquet_dir: Path) -> dict[int, int]:
    """Particiona y escribe TODO el dataset por año (modo FULL).

    Args:
        df: DataFrame Silver completo.
        parquet_dir: Directorio Gold.

    Returns:
        Diccionario {año: cantidad_registros}.
    """
    parquet_dir.mkdir(parents=True, exist_ok=True)
    years = df["anio"].unique().to_list()
    result: dict[int, int] = {}

    for year in sorted(years):
        year_df = df.filter(pl.col("anio") == year)
        year_df = year_df.drop("anio")
        output_path = parquet_dir / GOLD_PATTERN.format(year=year)
        year_df.write_parquet(output_path)
        count = len(year_df)
        result[year] = count
        logger.info("  contratos_%s.parquet: %d registros", year, count)

    return result


def _merge_gold_partition(
    parquet_dir: Path,
    year: int,
    updated_df: pl.DataFrame,
) -> int:
    """Actualiza incrementalmente una partición Gold para un año específico.

    1. Lee el Parquet existente para ese año.
    2. Realiza upsert por PRIMARY_KEY (los nuevos reemplazan a los existentes).
    3. Escribe el resultado actualizado.

    Args:
        parquet_dir: Directorio Gold.
        year: Año de la partición a actualizar.
        updated_df: DataFrame con registros actualizados para este año (sin columna anio).

    Returns:
        Cantidad final de registros en la partición.
    """
    gold_path = parquet_dir / GOLD_PATTERN.format(year=year)

    if not gold_path.exists():
        updated_df.write_parquet(gold_path)
        count = len(updated_df)
        logger.info("  contratos_%s.parquet (NUEVO): %d registros", year, count)
        return count

    # Leer partición existente
    existing = pl.read_parquet(gold_path)

    # Upsert: remover existentes con misma PK, concatenar nuevos
    if PRIMARY_KEY in existing.columns and PRIMARY_KEY in updated_df.columns:
        incoming_keys = set(updated_df[PRIMARY_KEY].to_list())
        kept = existing.filter(~pl.col(PRIMARY_KEY).is_in(incoming_keys))
        merged = pl.concat([kept, updated_df], how="diagonal_relaxed")
    else:
        logger.warning(
            "Columna '%s' no disponible en Gold año %d — reemplazo total.",
            PRIMARY_KEY,
            year,
        )
        merged = updated_df

    merged.write_parquet(gold_path)
    count = len(merged)
    logger.info(
        "  contratos_%s.parquet (ACTUALIZADO): %d registros (%d nuevos/actualizados)",
        year,
        count,
        len(updated_df),
    )
    return count


def _register_duckdb(
    parquet_dir: Path, con: Optional[duckdb.DuckDBPyConnection] = None
) -> Optional[duckdb.DuckDBPyConnection]:
    """Registra vista DuckDB 'contratos' sobre todos los Parquet Gold."""
    parquet_files = sorted(parquet_dir.glob("contratos_*.parquet"))
    if not parquet_files:
        logger.warning(
            "No se encontraron archivos Parquet Gold para registrar en DuckDB."
        )
        return con

    if con is None:
        con = duckdb.connect()

    files_str = ", ".join(f"'{str(f)}'" for f in parquet_files)
    query = (
        f"CREATE OR REPLACE VIEW contratos AS SELECT * FROM read_parquet([{files_str}])"
    )
    con.execute(query)

    count_result = con.execute("SELECT COUNT(*) FROM contratos").fetchone()
    total = count_result[0] if count_result else 0
    logger.info("Vista DuckDB 'contratos' registrada: %d registros totales", total)

    return con


def load_to_parquet(
    silver_path: Optional[Path] = None,
    parquet_dir: Optional[Path] = None,
    register_duckdb: bool = True,
    duckdb_con: Optional[duckdb.DuckDBPyConnection] = None,
) -> dict[int, int]:
    """Carga datos Silver → Gold: reemplazo total por año (modo FULL).

    Para carga incremental por año usar load_incremental().

    Args:
        silver_path: Ruta al archivo Silver (default: data/processed/contratos_silver.parquet).
        parquet_dir: Directorio de salida Gold (default: data/parquet/).
        register_duckdb: Si es True, registra la vista DuckDB al final.
        duckdb_con: Conexión DuckDB opcional.

    Returns:
        Diccionario {año: cantidad_registros}.
    """
    source = silver_path or _PROCESSED_DIR / SILVER_FILE
    target = parquet_dir or _PARQUET_DIR

    logger.info("=== Iniciando carga Silver → Gold (FULL) ===")

    df = _read_silver(source)
    _validate_silver(df)

    result = _partition_by_year_full(df, target)
    total = sum(result.values())
    logger.info(
        "Carga Gold completada: %d registros en %d particiones. Directorio: %s",
        total,
        len(result),
        target,
    )

    if register_duckdb:
        _register_duckdb(target, con=duckdb_con)

    return result


def load_incremental(
    df_silver: pl.DataFrame,
    affected_years: set[int],
    parquet_dir: Optional[Path] = None,
    register_duckdb: bool = True,
    duckdb_con: Optional[duckdb.DuckDBPyConnection] = None,
) -> dict[int, int]:
    """Carga incremental: actualiza solo las particiones Gold de años afectados.

    Args:
        df_silver: DataFrame Silver completo (ya mergeado).
        affected_years: Conjunto de años que recibieron cambios.
        parquet_dir: Directorio Gold (default: data/parquet/).
        register_duckdb: Si es True, registra la vista DuckDB.
        duckdb_con: Conexión DuckDB opcional.

    Returns:
        Diccionario {año: cantidad_registros} con los años actualizados.
    """
    target = parquet_dir or _PARQUET_DIR
    target.mkdir(parents=True, exist_ok=True)

    logger.info(
        "=== Iniciando carga incremental Gold: %d años afectados ===",
        len(affected_years),
    )

    result: dict[int, int] = {}

    for year in sorted(affected_years):
        year_df = df_silver.filter(pl.col("anio") == year)
        if len(year_df) == 0:
            logger.info("  Año %d: sin registros — se omite.", year)
            continue
        year_df = year_df.drop("anio")
        count = _merge_gold_partition(target, year, year_df)
        result[year] = count

    total = sum(result.values())
    logger.info(
        "Carga incremental Gold completada: %d registros en %d particiones.",
        total,
        len(result),
    )

    if register_duckdb:
        _register_duckdb(target, con=duckdb_con)

    return result
