"""Orquestador ETL — coordina el pipeline completo Extract → Transform → Load → Build Marts.

Soporta dos modos:
- FULL LOAD: primera ejecución o cuando no hay metadata previa.
- INCREMENTAL: descarga solo registros nuevos/modificados desde watermark.

Flujo:
    1. Extract  → socrata_extractor.extract_dataset() → data/raw/<run_id>/
    2. Transform → socrata_transformer.transform_*() → data/processed/
    3. Load      → parquet_loader.load_*() → data/parquet/ + DuckDB
    4. Build Marts → mart_builder.build_all_*() → data/marts/ + DuckDB Views
    5. Metadata  → actualiza etl_state.json + run_history.jsonl

Cada etapa registra:
- Hora de inicio y fin
- Cantidad de registros procesados
- Métricas de incrementalidad (inserts, updates, unchanged)
"""

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import duckdb
import polars as pl
from app.marts.mart_builder import MartBuilder

from etl.checkpoint import (
    create_run_checkpoint,
    determine_resume_action,
    find_latest_incomplete_run,
    mark_phase_completed,
)
from etl.extract.socrata_extractor import (
    DEFAULT_BASE_URL,
    DEFAULT_LIMIT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    extract_dataset,
)
from etl.load.parquet_loader import (
    load_incremental,
    load_to_parquet,
)
from etl.metadata import (
    append_run_history,
    generate_run_id,
    is_full_load_needed,
    load_etl_state,
    save_etl_state,
)
from etl.transform.socrata_transformer import (
    transform_incremental,
    transform_raw_files,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"
_PARQUET_DIR = _PROJECT_ROOT / "data" / "parquet"


def _compute_new_watermark(df, state: dict[str, Any]) -> Optional[str]:
    """Calcula el nuevo watermark como el máximo de ultima_actualizacion.

    Args:
        df: DataFrame Polars post-transform (Silver).
        state: Estado ETL actual.

    Returns:
        String ISO del max watermark, o el anterior si no hay datos nuevos.
    """
    watermark_col = "ultima_actualizacion"
    if watermark_col not in df.columns:
        logger.warning(
            "Columna '%s' no encontrada. Se mantiene el watermark anterior.",
            watermark_col,
        )
        return state.get("last_watermark")

    max_val = df[watermark_col].max()
    if max_val is None:
        return state.get("last_watermark")

    logger.info("Nuevo watermark calculado: %s", max_val)
    return str(max_val)


def _compute_affected_years(df: pl.DataFrame) -> set[int]:
    """Determina qué años fueron afectados por la ejecución actual."""

    if "anio" not in df.columns:
        return set()
    years = df["anio"].unique().drop_nulls().to_list()
    return set(years)


def run_etl(
    base_url: str = DEFAULT_BASE_URL,
    limit: int = DEFAULT_LIMIT,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    raw_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
    parquet_dir: Optional[Path] = None,
    force_full: bool = False,
) -> dict:
    """Ejecuta el pipeline ETL completo con soporte FULL/INCREMENTAL automático.

    Decide automáticamente si hacer FULL LOAD o INCREMENTAL basado en
    la metadata existente (etl_state.json).

    Args:
        base_url: URL base del dataset Socrata.
        limit: Tamaño de página para extracción.
        timeout: Timeout HTTP en segundos.
        max_retries: Reintentos máximos por página.
        raw_dir: Directorio base para datos crudos (default: data/raw/).
        processed_dir: Directorio para datos transformados (default: data/processed/).
        parquet_dir: Directorio para datos Gold (default: data/parquet/).
        force_full: Si es True, fuerza FULL LOAD incluso si hay metadata.

    Returns:
        Diccionario con el resumen del pipeline.
    """

    pipeline_start = time.monotonic()
    processed = processed_dir or _PROCESSED_DIR
    parquet = parquet_dir or _PARQUET_DIR

    # -------------------------------------------------------------------
    # Detectar ejecución previa fallida vía checkpoint
    # -------------------------------------------------------------------
    skip_extract = False
    skip_transform = False
    skip_load = False
    should_resume = False
    run_id = generate_run_id()
    prev_checkpoint_extract_meta: dict[str, Any] = {}

    incomplete_run = find_latest_incomplete_run()
    if incomplete_run:
        action, meta = determine_resume_action(incomplete_run)
        run_id = incomplete_run["run_id"]
        if action == "resume_transform":
            skip_extract = True
            prev_checkpoint_extract_meta = meta
            logger.info(
                "Checkpoint: Extract ya completado. Saltando a Transform. run_id=%s",
                run_id,
            )
        elif action == "resume_load":
            skip_extract = True
            skip_transform = True
            prev_checkpoint_extract_meta = meta
            logger.info(
                "Checkpoint: Extract y Transform ya completados. Saltando a Load. run_id=%s",
                run_id,
            )
        elif action == "resume_marts":
            skip_extract = True
            skip_transform = True
            skip_load = True
            prev_checkpoint_extract_meta = meta
            logger.info("Checkpoint: Saltando a Build Marts. run_id=%s", run_id)
        elif action == "resume_extract":
            should_resume = True
            prev_checkpoint_extract_meta = meta
            logger.info(
                "Checkpoint: Extract falló previamente. Reanudando extracción. run_id=%s",
                run_id,
            )
        # new_run: iniciar normalmente

    # -------------------------------------------------------------------
    # Determinar modo
    # -------------------------------------------------------------------
    state = load_etl_state()
    full_load = force_full or is_full_load_needed(state)

    mode = "FULL LOAD" if full_load else "INCREMENTAL"
    if skip_load:
        mode = "MARTS ONLY (RESUME)"
    elif skip_transform:
        mode = "LOAD (RESUME)"
    elif skip_extract:
        mode = "TRANSFORM (RESUME)"
    elif should_resume:
        mode = "FULL LOAD (RESUME)"

    # Crear checkpoint si es run nuevo
    if not incomplete_run or incomplete_run.get("status") == "completed":
        create_run_checkpoint(run_id, mode)

    logger.info("=" * 70)
    logger.info("PIPELINE ETL INICIADO — %s — run_id=%s", mode, run_id)
    logger.info("=" * 70)

    summary: dict[str, Any] = {
        "run_id": run_id,
        "mode": mode,
        "extract": {},
        "transform": {},
        "load": {},
        "marts": {},
    }

    duckdb_con = duckdb.connect()

    try:
        # ===================================================================
        # ETAPA 1: Extract
        # ===================================================================
        logger.info("-" * 50)
        logger.info("ETAPA 1/4: Extracción (Bronze)")
        logger.info("-" * 50)
        extract_start = time.monotonic()

        if skip_extract:
            # Usar metadata del checkpoint previo
            raw_path = prev_checkpoint_extract_meta.get("raw_path", "")
            run_dir = (
                Path(raw_path)
                if raw_path
                else (_PROJECT_ROOT / "data" / "raw" / run_id)
            )
            extracted_count = prev_checkpoint_extract_meta.get("rows", 0)
            extract_duration = 0.0
            logger.info(
                "ETAPA 1 SALTADA (ya completada): %d registros en %s",
                extracted_count,
                run_dir,
            )
        elif full_load:
            extracted_count, run_dir = extract_dataset(
                base_url=base_url,
                limit=limit,
                timeout=timeout,
                max_retries=max_retries,
                raw_dir=raw_dir,
                run_id=run_id,
                incremental=False,
                resume=should_resume,
            )
            extract_duration = time.monotonic() - extract_start
            mark_phase_completed(
                run_id,
                "extract",
                {
                    "rows": extracted_count,
                    "raw_path": str(run_dir),
                    "duration_seconds": round(extract_duration, 2),
                },
            )
        else:
            watermark = state.get("last_watermark")
            extracted_count, run_dir = extract_dataset(
                base_url=base_url,
                limit=limit,
                timeout=timeout,
                max_retries=max_retries,
                raw_dir=raw_dir,
                run_id=run_id,
                incremental=True,
                watermark=watermark,
                resume=should_resume,
            )
            extract_duration = time.monotonic() - extract_start
            mark_phase_completed(
                run_id,
                "extract",
                {
                    "rows": extracted_count,
                    "raw_path": str(run_dir),
                    "duration_seconds": round(extract_duration, 2),
                },
            )

        summary["extract"] = {
            "records": extracted_count,
            "run_dir": str(run_dir) if run_dir else "",
            "duration_seconds": round(extract_duration, 2),
        }
        logger.info(
            "ETAPA 1 COMPLETADA: %d registros en %.1fs",
            extracted_count,
            extract_duration,
        )

        # ===================================================================
        # ETAPA 2: Transform
        # ===================================================================
        logger.info("-" * 50)
        logger.info("ETAPA 2/4: Transformación (Silver)")
        logger.info("-" * 50)
        transform_start = time.monotonic()

        if skip_transform:
            # Cargar Silver existente para tener df_silver disponible
            silver_path = processed / "contratos_silver.parquet"
            if silver_path.exists():
                df_silver = pl.read_parquet(silver_path)
            else:
                df_silver = pl.DataFrame()
            merge_metrics = {"inserted": 0, "updated": 0, "unchanged": len(df_silver)}
            transform_duration = 0.0
            logger.info(
                "ETAPA 2 SALTADA (ya completada): %d registros en Silver",
                len(df_silver),
            )
        elif full_load:
            df_silver = transform_raw_files(
                raw_dir=run_dir,
                output_dir=processed,
            )
            merge_metrics = {"inserted": len(df_silver), "updated": 0, "unchanged": 0}
            transform_duration = time.monotonic() - transform_start
            mark_phase_completed(
                run_id,
                "transform",
                {
                    "rows": len(df_silver),
                    "inserted": merge_metrics["inserted"],
                    "duration_seconds": round(transform_duration, 2),
                },
            )
        else:
            df_silver, merge_metrics = transform_incremental(
                run_dir=run_dir,
                silver_dir=processed,
            )
            transform_duration = time.monotonic() - transform_start
            mark_phase_completed(
                run_id,
                "transform",
                {
                    "rows": len(df_silver),
                    "inserted": merge_metrics.get("inserted", 0),
                    "updated": merge_metrics.get("updated", 0),
                    "duration_seconds": round(transform_duration, 2),
                },
            )

        summary["transform"] = {
            "records": len(df_silver),
            "inserted": merge_metrics.get("inserted", 0),
            "updated": merge_metrics.get("updated", 0),
            "unchanged": merge_metrics.get("unchanged", 0),
            "duration_seconds": round(transform_duration, 2),
        }
        logger.info(
            "ETAPA 2 COMPLETADA: %d registros en %.1fs",
            len(df_silver),
            transform_duration,
        )

        # ===================================================================
        # ETAPA 3: Load
        # ===================================================================
        logger.info("-" * 50)
        logger.info("ETAPA 3/4: Carga (Gold + DuckDB)")
        logger.info("-" * 50)
        load_start = time.monotonic()

        if skip_load:
            affected_years = _compute_affected_years(df_silver)
            partitions = {}
            load_duration = 0.0
            total_gold = duckdb_con.execute(
                "SELECT COUNT(*) FROM contratos"
            ).fetchone()[0]
            logger.info(
                "ETAPA 3 SALTADA (ya completada): %d registros Gold", total_gold
            )
        elif full_load:
            partitions = load_to_parquet(
                silver_path=processed / "contratos_silver.parquet",
                parquet_dir=parquet,
                register_duckdb=True,
                duckdb_con=duckdb_con,
            )
            affected_years = set(partitions.keys())
            load_duration = time.monotonic() - load_start
            mark_phase_completed(
                run_id,
                "load",
                {
                    "partitions": {str(k): v for k, v in partitions.items()},
                    "total_records": sum(partitions.values()),
                    "duration_seconds": round(load_duration, 2),
                },
            )
        else:
            affected_years = _compute_affected_years(df_silver)
            if affected_years:
                partitions = load_incremental(
                    df_silver=df_silver,
                    affected_years=affected_years,
                    parquet_dir=parquet,
                    register_duckdb=True,
                    duckdb_con=duckdb_con,
                )
            else:
                logger.info("Sin años afectados — no se requiere carga Gold.")
                partitions = {}
            load_duration = time.monotonic() - load_start
            mark_phase_completed(
                run_id,
                "load",
                {
                    "partitions": {str(k): v for k, v in partitions.items()}
                    if partitions
                    else {},
                    "total_records": sum(partitions.values())
                    if partitions
                    else total_gold,
                    "duration_seconds": round(load_duration, 2),
                },
            )

        load_duration = time.monotonic() - load_start
        total_gold = duckdb_con.execute("SELECT COUNT(*) FROM contratos").fetchone()[0]
        summary["load"] = {
            "partitions": partitions,
            "total_records": total_gold,
            "years_affected": sorted(affected_years)
            if not full_load
            else sorted(partitions.keys()),
            "duration_seconds": round(load_duration, 2),
        }
        logger.info(
            "ETAPA 3 COMPLETADA: %d registros Gold en %.1fs",
            total_gold,
            load_duration,
        )

        # ===================================================================
        # ETAPA 4: Build Data Marts
        # ===================================================================
        logger.info("-" * 50)
        logger.info("ETAPA 4/4: Construcción de Data Marts")
        logger.info("-" * 50)
        mart_start = time.monotonic()

        mart_builder = MartBuilder()
        if full_load:
            mart_metrics = mart_builder.build_all_full(duckdb_con)
        else:
            mart_metrics = mart_builder.build_all_incremental(
                duckdb_con, affected_years
            )

        mart_duration = time.monotonic() - mart_start
        summary["marts"] = mart_metrics
        logger.info(
            "ETAPA 4 COMPLETADA: %d filas generadas en %.1fs",
            sum(mart_metrics.get("rows_generated", {}).values()),
            mart_duration,
        )

        # ===================================================================
        # Actualizar metadata
        # ===================================================================
        new_watermark = _compute_new_watermark(df_silver, state)

        new_state = {
            "last_run_id": run_id,
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_watermark": new_watermark,
            "last_silver_record_count": len(df_silver),
            "last_gold_record_count": total_gold,
            "last_processed_years": sorted(affected_years)
            if not full_load
            else sorted(partitions.keys()),
            "last_extract_records": extracted_count,
            "last_inserted_records": merge_metrics.get("inserted", 0),
            "last_updated_records": merge_metrics.get("updated", 0),
            "last_unchanged_records": merge_metrics.get("unchanged", 0),
            "marts": mart_metrics,
        }
        save_etl_state(new_state)

        # Registrar en historial
        total_duration = time.monotonic() - pipeline_start
        append_run_history(
            {
                "run_id": run_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "extract_records": extracted_count,
                "inserted_records": merge_metrics.get("inserted", 0),
                "updated_records": merge_metrics.get("updated", 0),
                "unchanged_records": merge_metrics.get("unchanged", 0),
                "years_affected": sorted(affected_years)
                if not full_load
                else sorted(partitions.keys()),
                "duration_seconds": round(total_duration, 2),
                "status": "completed",
            }
        )

        summary["total_duration_seconds"] = round(total_duration, 2)

        logger.info("=" * 70)
        logger.info("PIPELINE ETL COMPLETADO EXITOSAMENTE")
        logger.info("=" * 70)
        logger.info("  Modo:       %s", mode)
        logger.info("  Run ID:     %s", run_id)
        logger.info(
            "  Extract:    %d registros en %.1fs",
            summary["extract"].get("records", 0),
            summary["extract"].get("duration_seconds", 0),
        )
        logger.info(
            "  Transform:  %d registros en %.1fs",
            summary["transform"].get("records", 0),
            summary["transform"].get("duration_seconds", 0),
        )
        logger.info(
            "  Load:       %d registros Gold en %.1fs",
            summary["load"].get("total_records", 0),
            summary["load"].get("duration_seconds", 0),
        )
        logger.info(
            "  Marts:      %d filas en %.1fs",
            sum(mart_metrics.get("rows_generated", {}).values()),
            mart_metrics.get("duration_seconds", 0),
        )
        logger.info("  TOTAL:      %.1fs", total_duration)

        return summary

    except Exception:
        total_duration = time.monotonic() - pipeline_start
        logger.exception("PIPELINE FALLIDO después de %.1fs", total_duration)
        append_run_history(
            {
                "run_id": run_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": round(total_duration, 2),
                "status": "failed",
            }
        )
        raise

    finally:
        duckdb_con.close()


# ---------------------------------------------------------------------------
# Entry point para ejecución directa: python -m etl.orchestrator
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import logging as _logging

    _logging.basicConfig(
        level=_logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    run_etl()
