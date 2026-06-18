"""Módulo de transformación — capa Silver del pipeline ETL.

Responsable de normalizar los datos crudos (Bronze) aplicando:
- Casting de tipos (fechas, valores monetarios)
- Renombrado de columnas según el diccionario de datos
- Limpieza básica (trim, normalización de texto)
- Validaciones de calidad

Herramienta principal: Polars.
"""

from etl.transform.socrata_transformer import (
    merge_silver,
    transform_incremental,
    transform_raw_files,
)

__all__ = ["transform_raw_files", "transform_incremental", "merge_silver"]
