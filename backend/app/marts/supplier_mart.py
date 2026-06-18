"""SupplierMart — agregado analítico por proveedor + año.

Granularidad: 1 fila = 1 proveedor + 1 año.
"""

import duckdb
import polars as pl

from app.marts.base_mart import BaseMart, DataQualityError

SUPPLIER_MART_SQL = """
    SELECT
        documento_proveedor,
        MAX(proveedor_adjudicado) AS proveedor,
        YEAR(fecha_firma) AS anio,
        COUNT(*) AS total_contratos,
        SUM(valor_contrato) AS valor_total,
        AVG(valor_contrato) AS valor_promedio,
        COUNT(DISTINCT nit_entidad) AS entidades_unicas
    FROM contratos
    WHERE documento_proveedor IS NOT NULL
        AND proveedor_adjudicado IS NOT NULL
        AND fecha_firma IS NOT NULL
    GROUP BY documento_proveedor, YEAR(fecha_firma)
    ORDER BY anio, documento_proveedor
"""

SUPPLIER_INCREMENTAL_SQL = """
    SELECT
        documento_proveedor,
        MAX(proveedor_adjudicado) AS proveedor,
        YEAR(fecha_firma) AS anio,
        COUNT(*) AS total_contratos,
        SUM(valor_contrato) AS valor_total,
        AVG(valor_contrato) AS valor_promedio,
        COUNT(DISTINCT nit_entidad) AS entidades_unicas
    FROM contratos
    WHERE documento_proveedor IS NOT NULL
        AND proveedor_adjudicado IS NOT NULL
        AND fecha_firma IS NOT NULL
        AND YEAR(fecha_firma) IN ({years})
    GROUP BY documento_proveedor, YEAR(fecha_firma)
    ORDER BY anio, documento_proveedor
"""


class SupplierMart(BaseMart):
    """Data Mart de proveedores adjudicados."""

    name = "mart_proveedores"
    output_filename = "mart_proveedores.parquet"

    def build_full(self, conn: duckdb.DuckDBPyConnection) -> pl.DataFrame:
        df = conn.execute(SUPPLIER_MART_SQL).pl()
        self.save(df)
        self.register_view(conn)
        return df

    def build_incremental(
        self, conn: duckdb.DuckDBPyConnection, affected_years: set[int]
    ) -> pl.DataFrame:
        if not affected_years:
            return self._load_existing()

        years_str = ", ".join(str(y) for y in sorted(affected_years))
        sql = SUPPLIER_INCREMENTAL_SQL.format(years=years_str)
        new_df = conn.execute(sql).pl()

        existing = self._load_existing()
        merged = self._incremental_merge(existing, new_df, year_column="anio")
        self.save(merged)
        self.register_view(conn)
        return merged

    def _validate(self, df: pl.DataFrame) -> None:
        if len(df) == 0:
            return
        if df["valor_total"].min() < 0:
            raise DataQualityError(f"{self.name}: valor_total negativo detectado")
