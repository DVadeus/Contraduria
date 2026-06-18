"""BaseMart — clase abstracta para todos los Data Marts analíticos.

Define la interfaz común que todo mart debe implementar:
- build_full(): reconstrucción completa.
- build_incremental(): actualización solo de años afectados.
- _validate(): data quality checks.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import duckdb
import polars as pl

logger = logging.getLogger(__name__)


class DataQualityError(ValueError):
    """Error de validación de calidad en un Data Mart."""


class BaseMart(ABC):
    """Abstract base for all analytical Data Marts.

    Cada mart tiene:
    - name: identificador (ej. 'mart_entidades')
    - output_filename: archivo parquet de salida
    - mart_dir: directorio donde se persisten los marts
    """

    name: str
    output_filename: str

    def __init__(self, mart_dir: Path):
        self.mart_dir = mart_dir
        self.mart_dir.mkdir(parents=True, exist_ok=True)

    @property
    def output_path(self) -> Path:
        return self.mart_dir / self.output_filename

    @abstractmethod
    def build_full(self, conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
        """Reconstruye completamente el mart desde la vista `contratos`.

        Args:
            conn: Conexión DuckDB activa con la vista `contratos` registrada.

        Returns:
            DataFrame con todos los datos del mart.
        """
        ...

    @abstractmethod
    def build_incremental(
        self, conn: duckdb.DuckDBPyConnection, affected_years: set[int]
    ) -> pl.DataFrame:
        """Actualiza solo los años afectados del mart.

        Args:
            conn: Conexión DuckDB activa.
            affected_years: Años que recibieron cambios.

        Returns:
            DataFrame con el mart actualizado.
        """
        ...

    @abstractmethod
    def _validate(self, df: pl.DataFrame) -> None:
        """Valida la calidad de los datos del mart.

        Raises:
            DataQualityError: Si alguna validación falla.
        """
        ...

    def save(self, df: pl.DataFrame) -> None:
        """Guarda el DataFrame como Parquet y registra la vista DuckDB.

        Args:
            df: DataFrame a guardar.
        """
        self._validate(df)
        df.write_parquet(self.output_path)
        logger.info(
            "%s guardado: %d filas en %s",
            self.name,
            len(df),
            self.output_path,
        )

    def register_view(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Registra la vista DuckDB para este mart.

        Args:
            conn: Conexión DuckDB activa.
        """
        conn.execute(
            f"CREATE OR REPLACE VIEW {self.name} AS "
            f"SELECT * FROM read_parquet('{self.output_path}')"
        )
        count = conn.execute(f"SELECT COUNT(*) FROM {self.name}").fetchone()[0]
        logger.info("Vista DuckDB '%s' registrada: %d filas", self.name, count)

    def _incremental_merge(
        self,
        existing_df: pl.DataFrame,
        new_df: pl.DataFrame,
        year_column: str = "anio",
    ) -> pl.DataFrame:
        """Merge incremental estándar: elimina años afectados y concatena nuevos.

        Args:
            existing_df: DataFrame con el mart existente.
            new_df: DataFrame con los nuevos datos recalculados.
            year_column: Nombre de la columna de año.

        Returns:
            DataFrame mergeado.
        """
        if len(existing_df) == 0:
            return new_df

        # Filtrar años que NO están en los nuevos datos (se eliminan los viejos)
        years_to_remove = set(new_df[year_column].unique().to_list())
        kept = existing_df.filter(~pl.col(year_column).is_in(years_to_remove))

        result = pl.concat([kept, new_df], how="diagonal_relaxed")
        logger.debug(
            "%s merge: %d filas existentes, %d removidas (%d years), %d nuevas → %d total",
            self.name,
            len(existing_df),
            len(existing_df) - len(kept),
            len(years_to_remove),
            len(new_df),
            len(result),
        )
        return result

    def _load_existing(self) -> pl.DataFrame:
        """Carga el Parquet existente del mart. Retorna DataFrame vacío si no existe."""
        if self.output_path.exists():
            return pl.read_parquet(self.output_path)
        return pl.DataFrame()
