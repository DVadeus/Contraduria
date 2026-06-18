"""TemporalMart — agregado analítico por año + mes para dashboards temporales.

Granularidad: 1 fila = 1 año + 1 mes.
"""

import duckdb
import polars as pl

from app.marts.base_mart import BaseMart, DataQualityError

TEMPORAL_MART_SQL = """
    SELECT
        YEAR(fecha_firma) AS anio,
        MONTH(fecha_firma) AS mes,
        COUNT(*) AS total_contratos,
        SUM(valor_contrato) AS valor_total,
        AVG(valor_contrato) AS valor_promedio
    FROM contratos
    WHERE fecha_firma IS NOT NULL
    GROUP BY YEAR(fecha_firma), MONTH(fecha_firma)
    ORDER BY anio, mes
"""

TEMPORAL_INCREMENTAL_SQL = """
    SELECT
        YEAR(fecha_firma) AS anio,
        MONTH(fecha_firma) AS mes,
        COUNT(*) AS total_contratos,
        SUM(valor_contrato) AS valor_total,
        AVG(valor_contrato) AS valor_promedio
    FROM contratos
    WHERE fecha_firma IS NOT NULL
        AND YEAR(fecha_firma) IN ({years})
    GROUP BY YEAR(fecha_firma), MONTH(fecha_firma)
    ORDER BY anio, mes
"""


class TemporalMart(BaseMart):
    """Data Mart temporal (año + mes) para gráficos de evolución."""

    name = "mart_temporal"
    output_filename = "mart_temporal.parquet"

    def build_full(self, conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
        df = conn.execute(TEMPORAL_MART_SQL).pl()
        self.save(df)
        self.register_view(conn)
        return df

    def build_incremental(
        self, conn: duckdb.DuckDBPyConnection, affected_years: set[int]
    ) -> pl.DataFrame:
        if not affected_years:
            return self._load_existing()

        years_str = ", ".join(str(y) for y in sorted(affected_years))
        sql = TEMPORAL_INCREMENTAL_SQL.format(years=years_str)
        new_df = conn.execute(sql).pl()

        existing = self._load_existing()
        merged = self._incremental_merge(existing, new_df, year_column="anio")
        self.save(merged)
        self.register_view(conn)
        return merged

    def _validate(self, df: pl.DataFrame) -> None:
        if len(df) == 0:
            return
        if df["mes"].min() < 1 or df["mes"].max() > 12:
            raise DataQualityError(f"{self.name}: mes fuera del rango 1-12")
        if df["total_contratos"].min() < 0:
            raise DataQualityError(f"{self.name}: total_contratos negativo")
