"""Test de integración del pipeline ETL completo (Extract → Transform → Load).

Verifica el flujo end-to-end con un dataset simulado pequeño.
No depende de conectividad externa — usa datos mock.
"""

import json
from pathlib import Path

import duckdb
import polars as pl
import pytest
from etl.load.parquet_loader import load_to_parquet
from etl.transform.socrata_transformer import transform_raw_files


@pytest.fixture
def mock_raw_data(tmp_path: Path) -> Path:
    """Crea datos crudos simulados en tmp_path simulando salida del extractor."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)

    page1 = [
        {
            "id_contrato": "CO-BOG-001",
            "nombre_entidad": "Secretaría de Salud",
            "nit_entidad": "899999063",
            "proveedor_adjudicado": "PharmaColombia SAS",
            "documento_proveedor": "900123456",
            "fecha_de_firma": "2023-01-15T00:00:00.000",
            "fecha_de_inicio_del_contrato": "2023-02-01T00:00:00.000",
            "fecha_de_fin_del_contrato": "2023-12-31T00:00:00.000",
            "valor_del_contrato": "150000000.00",
            "valor_facturado": "120000000.00",
            "valor_pagado": "100000000.00",
            "estado_contrato": "Activo",
            "modalidad_de_contratacion": "Licitación Pública",
            "ciudad": "Bogotá D.C.",
            "departamento": "Bogotá",
        },
        {
            "id_contrato": "CO-BOG-002",
            "nombre_entidad": "Secretaría de Educación",
            "nit_entidad": "899999064",
            "proveedor_adjudicado": "EduTech Colombia",
            "fecha_de_firma": "2023-03-20T00:00:00.000",
            "valor_del_contrato": "80000000.00",
            "valor_pagado": "0.00",
            "estado_contrato": "Suspendido",
            "modalidad_de_contratacion": "Contratación Directa",
            "ciudad": "Bogotá D.C.",
        },
    ]

    page2 = [
        {
            "id_contrato": "CO-BOG-003",
            "nombre_entidad": "IDU",
            "nit_entidad": "800000001",
            "proveedor_adjudicado": "Obras Bogotá Ltda",
            "documento_proveedor": "800555123",
            "fecha_de_firma": "2024-06-01T00:00:00.000",
            "fecha_de_inicio_del_contrato": "2024-07-01T00:00:00.000",
            "fecha_de_fin_del_contrato": "2024-12-31T00:00:00.000",
            "valor_del_contrato": "300000000.00",
            "valor_facturado": "250000000.00",
            "valor_pagado": "200000000.00",
            "estado_contrato": "Activo",
            "modalidad_de_contratacion": "Licitación Pública",
            "ciudad": "Bogotá D.C.",
            "departamento": "Bogotá",
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

    return raw_dir


@pytest.mark.integration
def test_pipeline_bronze_silver_gold(mock_raw_data: Path, tmp_path: Path):
    """Pipeline completo: raw JSON → Silver Parquet → Gold particionado por año."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    parquet_dir = tmp_path / "data" / "parquet"

    # Crear conexión DuckDB compartida para todo el pipeline
    con = duckdb.connect()

    # -------------------------------------------------------------------
    # Etapa 1: Transform (Bronze → Silver)
    # -------------------------------------------------------------------
    df_silver = transform_raw_files(
        raw_dir=mock_raw_data,
        output_dir=processed_dir,
    )

    assert len(df_silver) == 3, "Debe haber 3 contratos en Silver"
    assert "fecha_firma" in df_silver.columns
    assert "valor_contrato" in df_silver.columns
    assert "anio" in df_silver.columns

    # Verificar transformaciones de tipos
    assert df_silver["fecha_firma"].dtype == pl.Date
    assert df_silver["valor_contrato"].dtype == pl.Float64

    # Verificar renombrado de columnas
    assert "fecha_de_firma" not in df_silver.columns
    assert "valor_del_contrato" not in df_silver.columns
    assert "fecha_firma" in df_silver.columns
    assert "valor_contrato" in df_silver.columns

    # Verificar años extraídos
    years = sorted(df_silver["anio"].unique().to_list())
    assert 2023 in years
    assert 2024 in years

    # Verificar que el archivo Silver existe
    silver_file = processed_dir / "contratos_silver.parquet"
    assert silver_file.exists()

    # -------------------------------------------------------------------
    # Etapa 2: Load (Silver → Gold) — usando la misma conexión DuckDB
    # -------------------------------------------------------------------
    partitions = load_to_parquet(
        silver_path=silver_file,
        parquet_dir=parquet_dir,
        register_duckdb=True,
        duckdb_con=con,
    )

    assert len(partitions) >= 2, (
        f"Debe haber al menos 2 particiones, hay {len(partitions)}"
    )
    assert partitions.get(2023, 0) > 0
    assert partitions.get(2024, 0) > 0

    # Verificar archivos Gold
    assert (parquet_dir / "contratos_2023.parquet").exists()
    assert (parquet_dir / "contratos_2024.parquet").exists()

    # -------------------------------------------------------------------
    # Etapa 3: Validar DuckDB — reutilizando la misma conexión
    # -------------------------------------------------------------------
    count = con.execute("SELECT COUNT(*) FROM contratos").fetchone()[0]
    assert count == 3, f"DuckDB debe tener 3 contratos, tiene {count}"

    # Consulta analítica simple
    result = con.execute("""
        SELECT
            YEAR(CAST(fecha_firma AS DATE)) AS anio_firma,
            COUNT(*) AS cantidad,
            SUM(valor_contrato) AS total_contratado
        FROM contratos
        GROUP BY anio_firma
        ORDER BY anio_firma
    """).fetchall()

    anios = {r[0] for r in result if r[0] is not None}
    assert 2023 in anios, f"Años encontrados: {anios}"
    assert 2024 in anios, f"Años encontrados: {anios}"

    con.close()


@pytest.mark.integration
def test_pipeline_handles_empty_raw_dir(tmp_path: Path):
    """El pipeline debe fallar apropiadamente si no hay datos raw."""
    import pytest

    with pytest.raises(FileNotFoundError, match="socrata_page_\\*\\.json"):
        transform_raw_files(raw_dir=tmp_path / "empty_raw")


@pytest.mark.integration
def test_pipeline_preserves_data_integrity(mock_raw_data: Path, tmp_path: Path):
    """Los datos no deben perder registros ni alterar valores en el pipeline."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    parquet_dir = tmp_path / "data" / "parquet"

    # Crear conexión DuckDB compartida
    con = duckdb.connect()

    # Transform
    df_silver = transform_raw_files(raw_dir=mock_raw_data, output_dir=processed_dir)

    # Load — usando la misma conexión DuckDB
    load_to_parquet(
        silver_path=processed_dir / "contratos_silver.parquet",
        parquet_dir=parquet_dir,
        register_duckdb=True,
        duckdb_con=con,
    )

    # Leer de vuelta desde DuckDB (misma conexión)
    df_db = con.execute(
        "SELECT id_contrato, valor_contrato, nombre_entidad FROM contratos ORDER BY id_contrato"
    ).fetchall()

    # Verificar registros específicos
    ids = [r[0] for r in df_db]
    assert "CO-BOG-001" in ids
    assert "CO-BOG-002" in ids
    assert "CO-BOG-003" in ids

    # Verificar valor no alterado del primer contrato
    co001 = [r for r in df_db if r[0] == "CO-BOG-001"][0]
    assert co001[1] == 150000000.00, f"Valor alterado: {co001[1]}"

    con.close()
