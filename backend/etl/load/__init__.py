"""Módulo de carga — capa Gold del pipeline ETL.

Responsable de:
- Leer datos Silver desde data/processed/
- Particionar por año en formato Parquet (data/parquet/)
- Registrar tablas virtuales en DuckDB para consultas analíticas
- Validar integridad de datos
"""

from etl.load.parquet_loader import load_to_parquet

__all__ = ["load_to_parquet"]
