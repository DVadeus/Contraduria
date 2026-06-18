"""Dependencias inyectables para Contraduria API.

Proporciona:
- get_db: inyección de conexión DuckDB por request.
- get_pagination: parámetros de paginación.
"""

from typing import Generator

import duckdb

from app.core.config import settings
from app.db.database import create_connection


def get_db() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """FastAPI dependency — inyecta conexión DuckDB gestionada por request.

    La conexión se cierra automáticamente al finalizar el request.
    """
    conn = create_connection(read_only=settings.duckdb_read_only)
    try:
        yield conn
    finally:
        conn.close()
