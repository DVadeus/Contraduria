"""EntityMart — agregado analítico por entidad + año.

Granularidad: 1 fila = 1 entidad + 1 año.
"""

import duckdb
import polars as pl

from app.marts.base_mart import BaseMart, DataQualityError

ENTITY_MART_SQL = """
    SELECT
        nit_entidad,
        MAX(nombre_entidad) AS nombre_entidad,
        YEAR(fecha_firma) AS anio,
        COUNT(*) AS total_contratos,
        SUM(valor_contrato) AS valor_total,
        AVG(valor_contrato) AS valor_promedio,
        MAX(valor_contrato) AS valor_maximo,
        MIN(valor_contrato) AS valor_minimo,
        COUNT(DISTINCT documento_proveedor) AS proveedores_unicos
    FROM contratos
    WHERE nit_entidad IS NOT NULL
        AND nombre_entidad IS NOT NULL
        AND fecha_firma IS NOT NULL
    GROUP BY nit_entidad, YEAR(fecha_firma)
    ORDER BY anio, nit_entidad
"""

ENTITY_MART_INCREMENTAL_SQL = """
    SELECT
        nit_entidad,
        MAX(nombre_entidad) AS nombre_entidad,
        YEAR(fecha_firma) AS anio,
        COUNT(*) AS total_contratos,
        SUM(valor_contrato) AS valor_total,
        AVG(valor_contrato) AS valor_promedio,
        MAX(valor_contrato) AS valor_maximo,
        MIN(valor_contrato) AS valor_minimo,
        COUNT(DISTINCT documento_proveedor) AS proveedores_unicos
    FROM contratos
    WHERE nit_entidad IS NOT NULL
        AND nombre_entidad IS NOT NULL
        AND fecha_firma IS NOT NULL
        AND YEAR(fecha_firma) IN ({years})
    GROUP BY nit_entidad, YEAR(fecha_firma)
    ORDER BY anio, nit_entidad
"""


class EntityMart(BaseMart):
    """Data Mart de entidades contratantes."""

    name = "mart_entidades"
    output_filename = "mart_entidades.parquet"

    def build_full(self, conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
        """Reconstruye completamente el mart de entidades."""
        df = conn.execute(ENTITY_MART_SQL).pl()
        self.save(df)
        self.register_view(conn)
        return df

    def build_incremental(
        self, conn: duckdb.DuckDBPyConnection, affected_years: set[int]
    ) -> pl.DataFrame:
        """Actualiza solo los años afectados del mart de entidades."""
        if not affected_years:
            return self._load_existing()

        years_str = ", ".join(str(y) for y in sorted(affected_years))
        sql = ENTITY_MART_INCREMENTAL_SQL.format(years=years_str)
        new_df = conn.execute(sql).pl()

        existing = self._load_existing()
        merged = self._incremental_merge(existing, new_df, year_column="anio")
        self.save(merged)
        self.register_view(conn)
        return merged

    def _validate(self, df: pl.DataFrame) -> None:
        """Valida: total_contratos >= 0, valor_total >= 0."""
        if len(df) == 0:
            return
        if df["total_contratos"].min() < 0:
            raise DataQualityError(f"{self.name}: total_contratos negativo detectado")
        if df["valor_total"].min() < 0:
            raise DataQualityError(f"{self.name}: valor_total negativo detectado")
