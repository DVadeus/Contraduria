"""MartBuilder — orquestador de Data Marts analíticos.

Coordina la construcción de los 4 Data Marts en modo FULL o INCREMENTAL,
registra las vistas DuckDB y retorna métricas.

Flujo:
    1. Recibe conexión DuckDB con vista `contratos` ya registrada.
    2. Ejecuta build_full() o build_incremental() en cada mart.
    3. Registra vistas DuckDB.
    4. Retorna métricas de construcción.
"""

import logging
import time
from pathlib import Path

import duckdb

from app.marts.entity_mart import EntityMart
from app.marts.modality_mart import ModalityMart
from app.marts.supplier_mart import SupplierMart
from app.marts.temporal_mart import TemporalMart

logger = logging.getLogger(__name__)

# Directorio de persistencia de marts
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_MARTS_DIR = _PROJECT_ROOT / "data" / "marts"


class MartBuilder:
    """Coordinador de construcción de Data Marts."""

    def __init__(self, marts_dir: Path | None = None):
        self.marts_dir = marts_dir or _MARTS_DIR
        self.marts_dir.mkdir(parents=True, exist_ok=True)

        self.entity = EntityMart(self.marts_dir)
        self.supplier = SupplierMart(self.marts_dir)
        self.temporal = TemporalMart(self.marts_dir)
        self.modality = ModalityMart(self.marts_dir)

        self._all_marts = [
            self.entity,
            self.supplier,
            self.temporal,
            self.modality,
        ]

    def build_all_full(self, conn: duckdb.DuckDBPyConnection) -> dict:
        """Construye los 4 marts en modo FULL (reconstrucción completa).

        Args:
            conn: Conexión DuckDB con vista `contratos` registrada.

        Returns:
            Diccionario con métricas:
            {
                "status": "success",
                "duration_seconds": float,
                "rows_generated": {name: int},
            }
        """
        logger.info("=" * 60)
        logger.info("BUILD MARTS: FULL LOAD")
        logger.info("=" * 60)

        build_start = time.monotonic()
        rows_generated: dict[str, int] = {}

        for mart in self._all_marts:
            logger.info("Building %s...", mart.name)
            mart_start = time.monotonic()
            df = mart.build_full(conn)
            rows = len(df)
            rows_generated[mart.name] = rows
            mart_duration = time.monotonic() - mart_start
            logger.info(
                "  %s: %d filas generadas en %.2fs",
                mart.name,
                rows,
                mart_duration,
            )

        duration = round(time.monotonic() - build_start, 2)
        logger.info(
            "BUILD MARTS COMPLETADO: %d filas totales en %.2fs",
            sum(rows_generated.values()),
            duration,
        )

        return {
            "status": "success",
            "duration_seconds": duration,
            "rows_generated": rows_generated,
        }

    def build_all_incremental(
        self,
        conn: duckdb.DuckDBPyConnection,
        affected_years: set[int],
    ) -> dict:
        """Construye marts en modo INCREMENTAL (solo años afectados).

        Args:
            conn: Conexión DuckDB con vista `contratos` registrada.
            affected_years: Años que recibieron cambios en esta ejecución.

        Returns:
            Diccionario con métricas.
        """
        logger.info("=" * 60)
        logger.info(
            "BUILD MARTS: INCREMENTAL LOAD (años: %s)",
            sorted(affected_years),
        )
        logger.info("=" * 60)

        build_start = time.monotonic()
        rows_generated: dict[str, int] = {}

        for mart in self._all_marts:
            logger.info("Building %s (incremental)...", mart.name)
            mart_start = time.monotonic()
            df = mart.build_incremental(conn, affected_years)
            rows = len(df)
            rows_generated[mart.name] = rows
            mart_duration = time.monotonic() - mart_start
            logger.info(
                "  %s: %d filas totales en %.2fs",
                mart.name,
                rows,
                mart_duration,
            )

        duration = round(time.monotonic() - build_start, 2)
        logger.info(
            "BUILD MARTS COMPLETADO: %d filas totales en %.2fs",
            sum(rows_generated.values()),
            duration,
        )

        return {
            "status": "success",
            "duration_seconds": duration,
            "rows_generated": rows_generated,
        }
