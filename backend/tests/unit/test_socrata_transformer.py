"""Tests unitarios para socrata_transformer.

Verifica:
- Carga de JSON crudos.
- Renombrado de columnas según diccionario.
- Cast de fechas a tipo Date.
- Cast de valores monetarios a Decimal.
- Limpieza de strings.
- Extracción de año desde fecha_firma.
"""

import json
from pathlib import Path

import polars as pl
from etl.transform.socrata_transformer import (
    _cast_dates,
    _cast_monetary,
    _clean_strings,
    _extract_year_from_fecha_firma,
    _load_raw_files,
    _rename_columns,
    transform_raw_files,
)

# ---------------------------------------------------------------------------
# Fixtures y helpers
# ---------------------------------------------------------------------------


def _create_sample_json_files(raw_dir: Path) -> None:
    """Crea archivos JSON de prueba en raw_dir simulando salida de Socrata."""
    page1 = [
        {
            "id_contrato": "CO-001",
            "nombre_entidad": "Secretaría de Salud",
            "fecha_de_firma": "2023-01-15T00:00:00.000",
            "fecha_de_inicio_del_contrato": "2023-02-01T00:00:00.000",
            "fecha_de_fin_del_contrato": "2023-12-31T00:00:00.000",
            "valor_del_contrato": "150000000.00",
            "valor_facturado": "75000000.00",
            "valor_pagado": "50000000.00",
        },
        {
            "id_contrato": "CO-002",
            "nombre_entidad": "  Secretaría de Educación  ",
            "fecha_de_firma": "2024-03-20T00:00:00.000",
            "valor_del_contrato": "80000000.00",
            "valor_pagado": "0.00",
        },
    ]
    page2 = [
        {
            "id_contrato": "CO-003",
            "nombre_entidad": "IDU",
            "fecha_de_firma": "2024-06-01T00:00:00.000",
            "fecha_de_inicio_del_contrato": "2024-07-01T00:00:00.000",
            "fecha_de_fin_del_contrato": "2024-12-31T00:00:00.000",
            "valor_del_contrato": "300000000.00",
            "valor_facturado": "100000000.00",
            "valor_pagado": "90000000.00",
        },
    ]

    with open(
        raw_dir / "socrata_page_000001_offset_0000000000.json", "w", encoding="utf-8"
    ) as f:
        json.dump(page1, f, ensure_ascii=False)

    with open(
        raw_dir / "socrata_page_000002_offset_0000050000.json", "w", encoding="utf-8"
    ) as f:
        json.dump(page2, f, ensure_ascii=False)


# ---------------------------------------------------------------------------
# _load_raw_files tests
# ---------------------------------------------------------------------------


class TestLoadRawFiles:
    """Tests para la función interna _load_raw_files."""

    def test_loads_all_json_files(self, tmp_path):
        """Debe cargar todos los archivos socrata_page_*.json y concatenarlos."""
        _create_sample_json_files(tmp_path)
        df = _load_raw_files(tmp_path)

        assert len(df) == 3
        assert "id_contrato" in df.columns

    def test_raises_when_no_files(self, tmp_path):
        """Debe lanzar FileNotFoundError si no hay archivos JSON."""
        import pytest

        with pytest.raises(FileNotFoundError, match="socrata_page_\\*\\.json"):
            _load_raw_files(tmp_path)

    def test_raises_when_all_files_empty(self, tmp_path):
        """Debe lanzar ValueError si todos los archivos están vacíos."""
        with open(
            tmp_path / "socrata_page_000001_offset_0000000000.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump([], f)

        import pytest

        with pytest.raises(ValueError, match="vacíos"):
            _load_raw_files(tmp_path)


# ---------------------------------------------------------------------------
# _rename_columns tests
# ---------------------------------------------------------------------------


class TestRenameColumns:
    """Tests para la función interna _rename_columns."""

    def test_renames_known_columns(self):
        """Debe renombrar columnas que están en COLUMN_RENAME_MAP."""
        df = pl.DataFrame(
            {"fecha_de_firma": ["2023-01-01"], "valor_del_contrato": ["1000"]}
        )
        result = _rename_columns(df)

        assert "fecha_firma" in result.columns
        assert "valor_contrato" in result.columns
        assert "fecha_de_firma" not in result.columns
        assert "valor_del_contrato" not in result.columns

    def test_preserves_unmapped_columns(self):
        """Debe conservar columnas que no están en el mapeo."""
        df = pl.DataFrame({"id_contrato": ["001"], "campo_desconocido": ["x"]})
        result = _rename_columns(df)

        assert "id_contrato" in result.columns
        assert "campo_desconocido" in result.columns

    def test_handles_empty_dataframe(self):
        """Debe funcionar con un DataFrame vacío."""
        df = pl.DataFrame()
        result = _rename_columns(df)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# _cast_dates tests
# ---------------------------------------------------------------------------


class TestCastDates:
    """Tests para la función interna _cast_dates."""

    def test_casts_iso_dates(self):
        """Debe convertir strings ISO 8601 a tipo Date."""
        df = pl.DataFrame(
            {
                "fecha_firma": ["2023-01-15T00:00:00.000"],
                "fecha_inicio": ["2023-02-01T00:00:00.000"],
                "fecha_fin": ["2023-12-31T00:00:00.000"],
            }
        )
        result = _cast_dates(df)

        assert result["fecha_firma"].dtype == pl.Date
        assert result["fecha_inicio"].dtype == pl.Date
        assert result["fecha_fin"].dtype == pl.Date

    def test_invalid_date_becomes_null(self):
        """Debe convertir a null fechas inválidas."""
        df = pl.DataFrame(
            {
                "fecha_firma": ["2023-01-15T00:00:00.000", "NO_ES_FECHA"],
            }
        )
        result = _cast_dates(df)

        assert result["fecha_firma"].dtype == pl.Date
        assert result["fecha_firma"][0] is not None
        assert result["fecha_firma"][1] is None


# ---------------------------------------------------------------------------
# _cast_monetary tests
# ---------------------------------------------------------------------------


class TestCastMonetary:
    """Tests para la función interna _cast_monetary."""

    def test_casts_string_to_float(self):
        """Debe convertir strings numéricos a Float64."""
        df = pl.DataFrame(
            {
                "valor_contrato": ["150000000.00"],
                "valor_pagado": ["0.00"],
            }
        )
        result = _cast_monetary(df)

        assert result["valor_contrato"].dtype == pl.Float64
        assert result["valor_contrato"][0] == 150000000.00
        assert result["valor_pagado"][0] == 0.00

    def test_non_numeric_becomes_null(self):
        """Debe convertir a null valores no numéricos."""
        df = pl.DataFrame(
            {
                "valor_contrato": ["1000.00", "N/A", "1500.50"],
            }
        )
        result = _cast_monetary(df)

        assert result["valor_contrato"][0] == 1000.00
        assert result["valor_contrato"][1] is None
        assert result["valor_contrato"][2] == 1500.50

    def test_handles_negative_values(self):
        """Debe manejar valores negativos correctamente."""
        df = pl.DataFrame({"valor_contrato": ["-5000.00"]})
        result = _cast_monetary(df)

        assert result["valor_contrato"][0] == -5000.00


# ---------------------------------------------------------------------------
# _clean_strings tests
# ---------------------------------------------------------------------------


class TestCleanStrings:
    """Tests para la función interna _clean_strings."""

    def test_trims_whitespace(self):
        """Debe eliminar espacios al inicio y final."""
        df = pl.DataFrame(
            {
                "nombre_entidad": ["  Secretaría de Salud  ", " IDU "],
            }
        )
        result = _clean_strings(df)

        assert result["nombre_entidad"][0] == "Secretaría de Salud"
        assert result["nombre_entidad"][1] == "IDU"

    def test_preserves_non_string_columns(self):
        """No debe modificar columnas no string."""
        df = pl.DataFrame({"id": [1, 2], "nombre": ["  A  ", " B "]})
        result = _clean_strings(df)

        assert result["id"][0] == 1


# ---------------------------------------------------------------------------
# _extract_year_from_fecha_firma tests
# ---------------------------------------------------------------------------


class TestExtractYear:
    """Tests para la función interna _extract_year_from_fecha_firma."""

    def test_extracts_year_from_date(self):
        """Debe extraer el año de una columna Date."""
        df = pl.DataFrame(
            {
                "fecha_firma": pl.Series(["2023-01-15", "2024-06-01"]).str.strptime(
                    pl.Date
                ),
            }
        )
        result = _extract_year_from_fecha_firma(df)

        assert "anio" in result.columns
        assert result["anio"].dtype == pl.Int32
        assert result["anio"][0] == 2023
        assert result["anio"][1] == 2024

    def test_null_date_maps_to_zero(self):
        """Debe asignar anio=0 si fecha_firma es null."""
        df = pl.DataFrame({"fecha_firma": pl.Series([None], dtype=pl.Date)})
        result = _extract_year_from_fecha_firma(df)

        assert result["anio"][0] == 0

    def test_missing_fecha_firma_uses_zero(self):
        """Debe asignar anio=0 a todos si fecha_firma no existe."""
        df = pl.DataFrame({"id": [1, 2]})
        result = _extract_year_from_fecha_firma(df)

        assert "anio" in result.columns
        assert result["anio"].to_list() == [0, 0]


# ---------------------------------------------------------------------------
# transform_raw_files integration test
# ---------------------------------------------------------------------------


class TestTransformRawFiles:
    """Tests de integración para la función pública transform_raw_files."""

    def test_full_transformation_pipeline(self, tmp_path):
        """Debe ejecutar el pipeline completo Bronze → Silver."""
        _create_sample_json_files(tmp_path)
        output_dir = tmp_path / "processed"
        output_dir.mkdir()

        df = transform_raw_files(raw_dir=tmp_path, output_dir=output_dir)

        # Verificar resultado
        assert len(df) == 3
        assert "fecha_firma" in df.columns
        assert "valor_contrato" in df.columns
        assert "anio" in df.columns

        # Verificar tipos
        assert df["fecha_firma"].dtype == pl.Date
        assert df["valor_contrato"].dtype == pl.Float64

        # Verificar años extraídos
        years = df["anio"].to_list()
        assert 2023 in years
        assert 2024 in years

        # Verificar archivo Silver creado
        silver_file = output_dir / "contratos_silver.parquet"
        assert silver_file.exists()

        # Verificar que se puede leer de vuelta
        df_read = pl.read_parquet(silver_file)
        assert len(df_read) == 3

    def test_string_trimming_applied(self, tmp_path):
        """Debe aplicar trim a los strings durante la transformación."""
        raw_file = tmp_path / "socrata_page_000001_offset_0000000000.json"
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {
                        "id_contrato": "CO-001",
                        "nombre_entidad": "  Secretaría de Salud  ",
                        "fecha_de_firma": "2023-01-15T00:00:00.000",
                        "valor_del_contrato": "1000.00",
                    }
                ],
                f,
                ensure_ascii=False,
            )

        output_dir = tmp_path / "processed"
        output_dir.mkdir()

        df = transform_raw_files(raw_dir=tmp_path, output_dir=output_dir)

        # Después del rename: nombre_entidad se mantiene igual (no está en el mapa)
        assert "nombre_entidad" in df.columns
        assert df["nombre_entidad"][0] == "Secretaría de Salud"
