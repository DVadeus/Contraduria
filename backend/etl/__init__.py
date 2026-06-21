"""Pipeline ETL de Contraduria — Extracción, Transformación y Carga de datos SECOP II.

Flujo principal:
    1. Extract  → Socrata API → data/raw/<run_id>/
    2. Transform → Polars       → data/processed/
    3. Load      → DuckDB/Parquet → data/parquet/
    4. Metadata  → data/metadata/

Soporta FULL LOAD (primera ejecución) e INCREMENTAL (watermark + row_hash upsert).

Entry point público:
    run_etl() — ejecuta el pipeline completo con detección automática de modo.

Para ejecutar el ETL:
    python -m etl.orchestrator          # FULL LOAD (primera ejecución)
    uv run python -m etl.orchestrator   # usando uv
"""
