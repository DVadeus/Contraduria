"""Módulo de extracción — capa Bronze del pipeline ETL.

Responsable de descargar los datos crudos desde la API Socrata de SECOP II
y almacenarlos en data/raw/ sin ninguna transformación.
"""

from etl.extract.socrata_extractor import (
    LOOKBACK_DAYS,
    WATERMARK_COLUMN,
    _create_run_directory,
    extract_dataset,
    fetch_page,
)

__all__ = [
    "extract_dataset",
    "fetch_page",
    "_create_run_directory",
    "WATERMARK_COLUMN",
    "LOOKBACK_DAYS",
]
