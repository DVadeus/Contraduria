"""ModalityMart — agregado analítico por modalidad + año con participación %.

Granularidad: 1 fila = 1 modalidad + 1 año.
La columna participacion_pct se calcula respecto al valor total del mismo año.
"""

import duckdb
import polars as pl

from app.marts.base_mart import BaseMart, DataQualityError

MODALITY_MART_SQL = """
    SELECT
        modalidad_contratacion AS modalidad,
        YEAR(fecha_firma) AS anio,
        COUNT(*) AS total_contratos,
        SUM(valor_contrato) AS valor_total
    FROM contratos
    WHERE modalidad_contratacion IS NOT NULL
        AND fecha_firma IS NOT NULL
    GROUP BY modalidad_contratacion, YEAR(fecha_firma)
    ORDER BY anio, modalidad
"""

MODALITY_INCREMENTAL_SQL = """
    SELECT
        modalidad_contratacion AS modalidad,
        YEAR(fecha_firma) AS anio,
        COUNT(*) AS total_contratos,
        SUM(valor_contrato) AS valor_total
    FROM contratos
    WHERE modalidad_contratacion IS NOT NULL
        AND fecha_firma IS NOT NULL
        AND YEAR(fecha_firma) IN ({years})
    GROUP BY modalidad_contratacion, YEAR(fecha_firma)
    ORDER BY anio, modalidad
"""


def _compute_participation(df: pl.DataFrame) -> pl.DataFrame:
    """Calcula participacion_pct como porcentaje del valor_total por año."""
    if len(df) == 0:
        return df.with_columns(pl.lit(0.0).alias("participacion_pct"))

    # Calcular total por año
    yearly_totals = df.group_by("anio").agg(
        pl.col("valor_total").sum().alias("total_anio")
    )

    df = df.join(yearly_totals, on="anio")
    df = df.with_columns(
        ((pl.col("valor_total") / pl.col("total_anio")) * 100.0).alias(
            "participacion_pct"
        )
    )
    return df.drop("total_anio")


class ModalityMart(BaseMart):
    """Data Mart de modalidades de contratación."""

    name = "mart_modalidades"
    output_filename = "mart_modalidades.parquet"

    def build_full(self, conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
        df = conn.execute(MODALITY_MART_SQL).pl()
        df = _compute_participation(df)
        self.save(df)
        self.register_view(conn)
        return df

    def build_incremental(
        self, conn: duckdb.DuckDBPyConnection, affected_years: set[int]
    ) -> pl.DataFrame:
        if not affected_years:
            return self._load_existing()

        years_str = ", ".join(str(y) for y in sorted(affected_years))
        sql = MODALITY_INCREMENTAL_SQL.format(years=years_str)
        new_df = conn.execute(sql).pl()

        existing = self._load_existing()
        merged = self._incremental_merge(existing, new_df, year_column="anio")

        # Recalcular participacion_pct sobre todo el dataset mergeado
        merged = _compute_participation(merged)

        self.save(merged)
        self.register_view(conn)
        return merged

    def _validate(self, df: pl.DataFrame) -> None:
        if len(df) == 0:
            return
        if "participacion_pct" in df.columns:
            pct_min = df["participacion_pct"].min()
            pct_max = df["participacion_pct"].max()
            if pct_min is not None and (pct_min < 0 or pct_max > 100):
                raise DataQualityError(
                    f"{self.name}: participacion_pct fuera de rango [0, 100] "
                    f"(min={pct_min}, max={pct_max})"
                )
