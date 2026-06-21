"""Checkpoint ETL — gestión del estado por fase de cada ejecución.

Proporciona persistencia granular del avance de cada run, permitiendo
reanudación automática desde la fase fallida sin reprocesar fases completadas.

Estructura en disco:
    data/metadata/runs/run_YYYYMMDD_HHMMSS.json

Formato del checkpoint:
{
    "run_id": "run_20260721_120000",
    "started_at": "2026-07-21T12:00:00+00:00",
    "status": "running",
    "mode": "FULL_LOAD",
    "phases": {
        "extract": {
            "status": "completed",
            "rows": 3250000,
            "raw_path": "data/raw/run_20260721_120000",
            "duration_seconds": 1800.5
        },
        "transform": {
            "status": "failed",
            "error": "MemoryError: ...",
            "duration_seconds": 45.2
        },
        "load": {
            "status": "pending"
        },
        "marts": {
            "status": "pending"
        }
    }
}

Uso en orchestrator:
    cp = create_run_checkpoint(run_id, mode)
    # ... Extract exitoso ...
    mark_phase_completed(run_id, "extract", {"rows": count, "raw_path": str(path)})
    # ... Transform falla ...
    mark_phase_failed(run_id, "transform", str(e))
    # En la siguiente ejecución:
    prev = find_latest_incomplete_run()
    if prev and prev["phases"]["extract"]["status"] == "completed":
        saltar_extract()
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_RUNS_DIR = _PROJECT_ROOT / "data" / "metadata" / "runs"

PHASES = ["extract", "transform", "load", "marts"]


def _runs_dir() -> Path:
    """Retorna el directorio de checkpoints, creándolo si no existe."""
    _RUNS_DIR.mkdir(parents=True, exist_ok=True)
    return _RUNS_DIR


def _checkpoint_path(run_id: str) -> Path:
    return _runs_dir() / f"{run_id}.json"


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------


def create_run_checkpoint(run_id: str, mode: str = "FULL_LOAD") -> dict[str, Any]:
    """Crea un checkpoint nuevo para la ejecución indicada.

    Args:
        run_id: ID único de la ejecución.
        mode: Modo del pipeline (FULL_LOAD, INCREMENTAL, FULL_LOAD_RESUME).

    Returns:
        Diccionario con el checkpoint inicial.
    """
    checkpoint: dict[str, Any] = {
        "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "mode": mode,
        "phases": {phase: {"status": "pending"} for phase in PHASES},
    }
    _write_checkpoint(run_id, checkpoint)
    logger.info("Checkpoint creado: %s", run_id)
    return checkpoint


def load_run_checkpoint(run_id: str) -> Optional[dict[str, Any]]:
    """Carga el checkpoint de una ejecución específica.

    Args:
        run_id: ID de la ejecución.

    Returns:
        Diccionario con el checkpoint, o None si no existe.
    """
    path = _checkpoint_path(run_id)
    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_phase_status(
    run_id: str,
    phase: str,
    status: str,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    """Actualiza el estado de una fase en el checkpoint.

    Args:
        run_id: ID de la ejecución.
        phase: Nombre de la fase (extract, transform, load, marts).
        status: Nuevo estado (running, completed, failed).
        extra: Metadatos adicionales (rows, raw_path, duration_seconds, error, etc.).
    """
    checkpoint = load_run_checkpoint(run_id)
    if checkpoint is None:
        logger.warning(
            "Intento de actualizar checkpoint inexistente: %s/%s", run_id, phase
        )
        return

    checkpoint["phases"][phase]["status"] = status
    if extra:
        checkpoint["phases"][phase].update(extra)

    # Si la fase falló, marcar el run como failed
    if status == "failed":
        checkpoint["status"] = "failed"

    _write_checkpoint(run_id, checkpoint)
    logger.debug("Checkpoint actualizado: %s/%s → %s", run_id, phase, status)


def mark_phase_completed(
    run_id: str,
    phase: str,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """Marca una fase como completada exitosamente."""
    update_phase_status(run_id, phase, "completed", metadata)


def mark_phase_failed(
    run_id: str,
    phase: str,
    error: str,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """Marca una fase como fallida con el error correspondiente."""
    extra = {"error": error}
    if metadata:
        extra.update(metadata)
    update_phase_status(run_id, phase, "failed", extra)


def mark_run_completed(run_id: str) -> None:
    """Marca la ejecución completa como finalizada."""
    checkpoint = load_run_checkpoint(run_id)
    if checkpoint is None:
        return
    checkpoint["status"] = "completed"
    checkpoint["completed_at"] = datetime.now(timezone.utc).isoformat()
    _write_checkpoint(run_id, checkpoint)
    logger.info("Checkpoint marcado como completado: %s", run_id)


def find_latest_incomplete_run() -> Optional[dict[str, Any]]:
    """Busca la ejecución más reciente que no se haya completado.

    Returns:
        Diccionario con el checkpoint de la ejecución incompleta,
        o None si todas las ejecuciones están completadas o no hay ninguna.
    """
    runs_dir = _runs_dir()
    checkpoint_files = sorted(runs_dir.glob("*.json"), reverse=True)
    if not checkpoint_files:
        return None

    for f in checkpoint_files:
        with open(f, "r", encoding="utf-8") as fh:
            checkpoint = json.load(fh)
        if checkpoint.get("status") != "completed":
            run_id = checkpoint.get("run_id", f.stem)
            logger.info(
                "Ejecución incompleta encontrada: %s (status=%s)",
                run_id,
                checkpoint.get("status"),
            )
            return checkpoint

    return None


def determine_resume_action(
    checkpoint: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Determina qué acción tomar para reanudar una ejecución incompleta.

    Args:
        checkpoint: Checkpoint de la ejecución incompleta.

    Returns:
        Tupla (acción, metadatos) donde acción es:
        - "resume_extract": reanudar extracción
        - "resume_transform": saltar extract, reanudar transform
        - "resume_load": saltar extract y transform, reanudar load
        - "resume_marts": saltar todo excepto marts
        - "new_run": iniciar ejecución nueva
    """
    phases = checkpoint.get("phases", {})

    extract_status = phases.get("extract", {}).get("status", "pending")
    transform_status = phases.get("transform", {}).get("status", "pending")
    load_status = phases.get("load", {}).get("status", "pending")
    marts_status = phases.get("marts", {}).get("status", "pending")

    if extract_status == "failed":
        return "resume_extract", checkpoint["phases"]["extract"]

    if transform_status == "failed":
        return "resume_transform", checkpoint["phases"]["extract"]

    if load_status == "failed":
        return "resume_load", checkpoint["phases"]["extract"]

    if marts_status == "failed":
        return "resume_marts", checkpoint["phases"]["extract"]

    # Si extract está completed pero transform está pending
    # (el pipeline fue interrumpido externamente)
    if extract_status == "completed" and transform_status == "pending":
        return "resume_transform", checkpoint["phases"]["extract"]

    if (
        extract_status == "completed"
        and transform_status == "completed"
        and load_status == "pending"
    ):
        return "resume_load", checkpoint["phases"]["extract"]

    return "new_run", {}


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _write_checkpoint(run_id: str, checkpoint: dict[str, Any]) -> None:
    """Escribe el checkpoint a disco de forma atómica."""
    path = _checkpoint_path(run_id)
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2, default=str)
    tmp_path.replace(path)
