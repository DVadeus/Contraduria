"""Tests unitarios para parquet_loader.

Verifica:
- Lectura de archivo Silver.
- Validación de integridad.
- Particionado por año.
- Escritura de archivos Parquet Gold.
- Registro en DuckDB.
"""

import polars as pl
import pytest
from etl.load.parquet_loader import (
    _partition_by_year_full,
    _read_silver,
    _register_duckdb,
    _validate_silver,
    load_to_parquet,
)

# ---------------------------------------------------------------------------
# _read_silver tests
# ---------------------------------------------------------------------------


class TestReadSilver:
    """Tests para la función interna _read_silver."""

    def test_reads_existing_file(self, tmp_path):
        """Debe leer un archivo Parquet Silver existente."""
        df = pl.DataFrame(
            {
                "id_contrato": ["001", "002"],
                "anio": [2023, 2024],
                "valor_contrato": [1000.0, 2000.0],
            }
        )
        silver_path = tmp_path / "contratos_silver.parquet"
        df.write_parquet(silver_path)

        result = _read_silver(silver_path)
        assert len(result) == 2
        assert result["id_contrato"].to_list() == ["001", "002"]

    def test_raises_when_file_not_found(self, tmp_path):
        """Debe lanzar FileNotFoundError si el archivo no existe."""
        with pytest.raises(FileNotFoundError, match="Silver no encontrado"):
            _read_silver(tmp_path / "inexistente.parquet")


# ---------------------------------------------------------------------------
# _validate_silver tests
# ---------------------------------------------------------------------------


class TestValidateSilver:
    """Tests para la función interna _validate_silver."""

    def test_passes_with_valid_data(self):
        """Debe validar sin errores un dataset Silver correcto."""
        df = pl.DataFrame(
            {
                "id_contrato": ["001"],
                "anio": [2023],
                "valor_contrato": [1000.0],
            }
        )
        # No debe lanzar excepción
        _validate_silver(df)

    def test_raises_when_empty(self):
        """Debe lanzar ValueError si el dataset está vacío."""
        df = pl.DataFrame()
        with pytest.raises(ValueError, match="vacío"):
            _validate_silver(df)

    def test_raises_when_missing_anio(self):
        """Debe lanzar ValueError si falta la columna anio."""
        df = pl.DataFrame({"id_contrato": ["001"]})
        with pytest.raises(ValueError, match="Columna 'anio' no encontrada"):
            _validate_silver(df)

    def test_warns_when_missing_id_contrato(self, caplog):
        """Debe emitir warning si falta id_contrato pero no fallar."""
        df = pl.DataFrame({"anio": [2023]})
        _validate_silver(df)
        assert "id_contrato" in caplog.text


# ---------------------------------------------------------------------------
# _partition_by_year tests
# ---------------------------------------------------------------------------


class TestPartitionByYear:
    """Tests para la función interna _partition_by_year_full."""

    def test_partitions_by_year(self, tmp_path):
        """Debe particionar correctamente por año."""
        df = pl.DataFrame(
            {
                "id_contrato": ["001", "002", "003"],
                "anio": [2023, 2024, 2023],
                "valor_contrato": [1000.0, 2000.0, 3000.0],
            }
        )

        result = _partition_by_year_full(df, tmp_path)

        assert len(result) == 2
        assert result[2023] == 2
        assert result[2024] == 1

        # Verificar archivos creados
        assert (tmp_path / "contratos_2023.parquet").exists()
        assert (tmp_path / "contratos_2024.parquet").exists()

        # Verificar contenido
        df_2023 = pl.read_parquet(tmp_path / "contratos_2023.parquet")
        assert len(df_2023) == 2
        assert "anio" not in df_2023.columns  # Columna de particionado removida

        df_2024 = pl.read_parquet(tmp_path / "contratos_2024.parquet")
        assert len(df_2024) == 1

    def test_single_year(self, tmp_path):
        """Debe manejar un solo año."""
        df = pl.DataFrame(
            {
                "id_contrato": ["001"],
                "anio": [2023],
            }
        )

        result = _partition_by_year_full(df, tmp_path)

        assert result == {2023: 1}
        assert (tmp_path / "contratos_2023.parquet").exists()

    def test_year_zero(self, tmp_path):
        """Debe manejar registros con anio=0 (fecha desconocida)."""
        df = pl.DataFrame(
            {
                "id_contrato": ["001", "002"],
                "anio": [0, 0],
            }
        )

        result = _partition_by_year_full(df, tmp_path)

        assert result == {0: 2}
        assert (tmp_path / "contratos_0.parquet").exists()


# ---------------------------------------------------------------------------
# _register_duckdb tests
# ---------------------------------------------------------------------------


class TestRegisterDuckDB:
    """Tests para la función interna _register_duckdb."""

    def test_registers_view(self, tmp_path):
        """Debe registrar una vista DuckDB sobre los Parquet Gold."""
        df = pl.DataFrame(
            {
                "id_contrato": ["001", "002"],
                "nombre_entidad": ["Sec. Salud", "IDU"],
                "valor_contrato": [1000.0, 2000.0],
            }
        )
        df.write_parquet(tmp_path / "contratos_2023.parquet")

        con = _register_duckdb(tmp_path)
        assert con is not None

        result = con.execute("SELECT COUNT(*) FROM contratos").fetchone()
        assert result[0] == 2

        # Verificar columnas
        cols = con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'contratos' ORDER BY column_name"
        ).fetchall()
        col_names = [c[0] for c in cols]
        assert "id_contrato" in col_names
        assert "nombre_entidad" in col_names
        con.close()

    def test_no_files_no_error(self, tmp_path):
        """No debe lanzar error si no hay archivos Parquet."""
        _register_duckdb(tmp_path)  # No debe fallar


# ---------------------------------------------------------------------------
# load_to_parquet integration test
# ---------------------------------------------------------------------------


class TestLoadToParquet:
    """Tests de integración para la función pública load_to_parquet."""

    def test_full_load_pipeline(self, tmp_path):
        """Debe ejecutar el pipeline Silver → Gold completo."""
        # Crear Silver de prueba
        silver_dir = tmp_path / "processed"
        silver_dir.mkdir()
        df_silver = pl.DataFrame(
            {
                "id_contrato": ["001", "002", "003"],
                "nombre_entidad": ["Sec. Salud", "IDU", "Sec. Educación"],
                "anio": [2023, 2024, 2023],
                "valor_contrato": [1000.0, 2000.0, 3000.0],
                "fecha_firma": pl.Series(
                    ["2023-01-15", "2024-06-01", "2023-12-01"]
                ).str.strptime(pl.Date),
            }
        )
        df_silver.write_parquet(silver_dir / "contratos_silver.parquet")

        parquet_dir = tmp_path / "parquet"

        result = load_to_parquet(
            silver_path=silver_dir / "contratos_silver.parquet",
            parquet_dir=parquet_dir,
            register_duckdb=True,
        )

        assert result == {2023: 2, 2024: 1}

        # Verificar archivos Gold
        assert (parquet_dir / "contratos_2023.parquet").exists()
        assert (parquet_dir / "contratos_2024.parquet").exists()

    def test_raises_when_silver_not_found(self, tmp_path):
        """Debe lanzar FileNotFoundError si Silver no existe."""
        with pytest.raises(FileNotFoundError, match="Silver no encontrado"):
            load_to_parquet(
                silver_path=tmp_path / "inexistente.parquet",
                parquet_dir=tmp_path / "parquet",
            )
