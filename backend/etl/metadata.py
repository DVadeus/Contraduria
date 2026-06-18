"""Metadata ETL — gestión del estado del pipeline y registro histórico de ejecuciones.

Responsable de:
- Cargar/guardar etl_state.json con watermark, conteos y contexto de última ejecución.
- Registrar cada ejecución en run_history.jsonl para auditoría.
- Proveer defaults para la primera ejecución (FULL LOAD).

Formato de etl_state.json:
{
    "last_run_id": "run_20260717_210500",
    "last_run": "2026-07-17T21:05:00",
    "last_watermark": "2026-07-15T00:00:00.000",
    "last_silver_record_count": 1523400,
    "last_gold_record_count": 1523400,
    "last_processed_years": [2021, 2022, 2023, 2024, 2025, 2026],
    "last_extract_records": 620,
    "last_inserted_records": 500,
    "last_updated_records": 120,
    "last_unchanged_records": 0
}

Formato de run_history.jsonl (una línea por ejecución):
{
    "run_id": "run_20260717_210500",
    "timestamp": "2026-07-17T21:05:00",
    "extract_records": 620,
    "inserted_records": 500,
    "updated_records": 120,
    "unchanged_records": 0,
    "years_affected": [2025, 2026],
    "duration_seconds": 45.2,
    "status": "completed"
}
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rutas por defecto
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_METADATA_DIR = _PROJECT_ROOT / "data" / "metadata"
_STATE_FILE = "etl_state.json"
_HISTORY_FILE = "run_history.jsonl"

# ---------------------------------------------------------------------------
# Funciones públicas
# ---------------------------------------------------------------------------


def get_metadata_dir() -> Path:
    """Retorna el directorio de metadata, creándolo si no existe."""
    _METADATA_DIR.mkdir(parents=True, exist_ok=True)
    return _METADATA_DIR


def _state_path() -> Path:
    return get_metadata_dir() / _STATE_FILE


def _history_path() -> Path:
    return get_metadata_dir() / _HISTORY_FILE


def load_etl_state() -> dict[str, Any]:
    """Carga el estado actual del ETL desde etl_state.json.

    Si el archivo no existe, retorna un diccionario vacío indicando
    que se requiere FULL LOAD.

    Returns:
        Diccionario con el estado, o {} si es primera ejecución.
    """
    path = _state_path()
    if not path.exists():
        logger.info("No se encontró etl_state.json — se requiere FULL LOAD.")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        state = json.load(f)
    logger.info(
        "Estado ETL cargado: last_run=%s, watermark=%s, silver_count=%d",
        state.get("last_run", "N/A"),
        state.get("last_watermark", "N/A"),
        state.get("last_silver_record_count", 0),
    )
    return state


def save_etl_state(state: dict[str, Any]) -> None:
    """Guarda el estado del ETL en etl_state.json.

    Args:
        state: Diccionario con el estado actualizado.
    """
    path = _state_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, default=str)
    logger.info("Estado ETL guardado en %s", path)


def append_run_history(entry: dict[str, Any]) -> None:
    """Agrega una línea al historial de ejecuciones (JSONL).

    Args:
        entry: Diccionario con los datos de la ejecución.
    """
    path = _history_path()
    with open(path, "a", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, default=str)
        f.write("\n")
    logger.info("Ejecución registrada en historial: %s", entry.get("run_id", "unknown"))


def create_default_state() -> dict[str, Any]:
    """Crea un estado inicial vacío para la primera ejecución (FULL LOAD)."""
    return {
        "last_run_id": None,
        "last_run": None,
        "last_watermark": None,
        "last_silver_record_count": 0,
        "last_gold_record_count": 0,
        "last_processed_years": [],
        "last_extract_records": 0,
        "last_inserted_records": 0,
        "last_updated_records": 0,
        "last_unchanged_records": 0,
    }


def generate_run_id() -> str:
    """Genera un ID único de ejecución basado en timestamp.

    Returns:
        String en formato 'run_YYYYMMDD_HHMMSS'.
    """
    now = datetime.now(timezone.utc)
    return now.strftime("run_%Y%m%d_%H%M%S")


def is_full_load_needed(state: dict[str, Any]) -> bool:
    """Determina si se requiere FULL LOAD basado en el estado actual.

    Args:
        state: Estado cargado desde etl_state.json.

    Returns:
        True si no hay estado previo o el watermark es None.
    """
    if not state:
        return True
    return state.get("last_watermark") is None
