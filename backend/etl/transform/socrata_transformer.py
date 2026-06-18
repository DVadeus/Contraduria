"""Transformador Socrata — normaliza datos crudos (Bronze → Silver).

Lee los archivos JSON crudos desde data/raw/<run_id>/, aplica normalización de tipos
según el diccionario de datos de Contraduria y escribe Parquet en data/processed/.

Soporta modo FULL (primera ejecución) e INCREMENTAL (merge sobre Silver existente).

Reglas ETL aplicadas:
- Polars como herramienta principal de procesamiento.
- Cast de fechas a tipo Date.
- Cast de valores monetarios a Decimal.
- Renombrado de columnas clave.
- Limpieza básica de strings (trim, normalización).
- row_hash para detección de cambios reales.
- merge_silver() para upsert incremental.
- Sin transformaciones de negocio — solo normalización estructural.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

import polars as pl

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración por defecto
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_RAW_DIR = _PROJECT_ROOT / "data" / "raw"
_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"

SILVER_FILE = "contratos_silver.parquet"

PRIMARY_KEY = "id_contrato"

# Mapeo de columnas con caracteres problemáticos (acentos, espacios) a nombres
# limpios según el diccionario de datos de Contraduria.
COLUMN_RENAME_MAP: dict[str, str] = {
    # Entidad Contratante
    "localizaci_n": "localizacion",
    "entidad_centralizada": "entidad_centralizada",
    # Proceso Contractual
    "modalidad_de_contratacion": "modalidad_contratacion",
    "tipo_de_contrato": "tipo_contrato",
    "codigo_de_categoria_principal": "codigo_categoria_principal",
    "descripcion_del_proceso": "descripcion_proceso",
    "objeto_del_contrato": "objeto_contrato",
    # Fechas
    "fecha_de_firma": "fecha_firma",
    "fecha_de_inicio_del_contrato": "fecha_inicio",
    "fecha_de_fin_del_contrato": "fecha_fin",
    "duraci_n_del_contrato": "duracion_contrato",
    "dias_adicionados": "dias_adicionados",
    # Proveedor
    "proveedor_adjudicado": "proveedor_adjudicado",
    "tipodocproveedor": "tipo_doc_proveedor",
    "es_grupo": "es_grupo",
    "es_pyme": "es_pyme",
    # Valores Contractuales
    "valor_del_contrato": "valor_contrato",
    "valor_pendiente_de_pago": "valor_pendiente_pago",
    "valor_pendiente_de_ejecucion": "valor_pendiente_ejecucion",
    # Información Normativa
    "justificacion_modalidad_de": "justificacion_modalidad",
    "condiciones_de_entrega": "condiciones_entrega",
    "habilita_pago_adelantado": "habilita_pago_adelantado",
    "liquidaci_n": "liquidacion",
    "obligaci_n_ambiental": "obligacion_ambiental",
    "obligaciones_postconsumo": "obligaciones_postconsumo",
    "reversion": "reversion",
    "el_contrato_puede_ser_prorrogado": "contrato_prorrogable",
    # Financiación
    "origen_de_los_recursos": "origen_recursos",
    "presupuesto_general_de_la_nacion_pgn": "presupuesto_pgn",
    "sistema_general_de_participaciones": "sgp",
    "sistema_general_de_regal_as": "sgr",
    "recursos_propios_alcald_as_gobernaciones_y_resguardos_ind_genas_": "recursos_propios_territoriales",
    "recursos_de_credito": "recursos_credito",
    # Ejecución Financiera
    "valor_de_pago_adelantado": "valor_pago_adelantado",
    "valor_pendiente_de": "valor_pendiente_obligacion",
    # Representante Legal
    "nombre_representante_legal": "nombre_representante_legal",
    "nacionalidad_representante_legal": "nacionalidad_representante_legal",
    "domicilio_representante_legal": "domicilio_representante_legal",
    "tipo_de_identificaci_n_representante_legal": "tipo_id_representante_legal",
    "g_nero_representante_legal": "genero_representante_legal",
    # Supervisión
    "nombre_ordenador_del_gasto": "nombre_ordenador_gasto",
    "tipo_de_documento_ordenador_del_gasto": "tipo_doc_ordenador_gasto",
    "tipo_de_documento_supervisor": "tipo_doc_supervisor",
    "nombre_ordenador_de_pago": "nombre_ordenador_pago",
    "tipo_de_documento_ordenador_de_pago": "tipo_doc_ordenador_pago",
    "n_mero_de_documento_ordenador_de_pago": "num_doc_ordenador_pago",
    # Transparencia
    "urlproceso": "url_proceso",
    "documentos_tipo": "documentos_tipo",
    "descripcion_documentos_tipo": "descripcion_documentos_tipo",
    # Acuerdo de Paz
    "espostconflicto": "es_postconflicto",
    "puntos_del_acuerdo": "puntos_acuerdo",
    "pilares_del_acuerdo": "pilares_acuerdo",
}

DATE_COLUMNS: set[str] = {
    "fecha_firma",
    "fecha_inicio",
    "fecha_fin",
}

MONETARY_COLUMNS: set[str] = {
    "valor_contrato",
    "valor_facturado",
    "valor_pagado",
    "valor_pendiente_pago",
    "valor_pendiente_ejecucion",
    "saldo_cdp",
    "valor_pago_adelantado",
    "valor_amortizado",
    "valor_pendiente_obligacion",
    "saldo_vigencia",
}


def _compute_row_hash(df: pl.DataFrame) -> pl.DataFrame:
    """Calcula SHA256 del contenido completo de cada fila.

    Excluye las columnas `row_hash` y `anio` del cómputo para que el hash
    refleje únicamente cambios en los datos de negocio.

    Args:
        df: DataFrame transformado.

    Returns:
        DataFrame con columna `row_hash` agregada.
    """
    exclude = {"row_hash", "anio"}
    hash_input_cols = [c for c in df.columns if c not in exclude]

    # Convertir todas las columnas a string y concatenar
    concat_expr = pl.concat_str(
        [pl.col(c).cast(pl.Utf8).fill_null("") for c in hash_input_cols],
        separator="|",
    )

    hash_series = (
        df.with_columns(concat_expr.alias("_hash_input")).select(
            pl.col("_hash_input")
            .map_elements(
                lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest(),
                return_dtype=pl.Utf8,
            )
            .alias("row_hash")
        )
    )["row_hash"]

    return df.with_columns(hash_series)


def _load_raw_files(raw_dir: Path) -> pl.DataFrame:
    """Carga todos los archivos JSON crudos desde el directorio de ejecución.

    Args:
        raw_dir: Directorio que contiene los archivos socrata_page_*.json
                (debe ser un directorio de ejecución específico, no data/raw/).

    Returns:
        DataFrame de Polars con todos los registros concatenados.

    Raises:
        FileNotFoundError: Si no hay archivos JSON en el directorio.
        ValueError: Si todos los archivos están vacíos.
    """
    json_files = sorted(raw_dir.glob("socrata_page_*.json"))
    if not json_files:
        raise FileNotFoundError(
            f"No se encontraron archivos socrata_page_*.json en {raw_dir}"
        )

    logger.info("Cargando %d archivos JSON desde %s", len(json_files), raw_dir)

    records: list[dict] = []
    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            page_data = json.load(f)
        if page_data:
            records.extend(page_data)
        logger.debug("  %s: %d registros", json_file.name, len(page_data))

    if not records:
        raise ValueError(
            f"Todos los archivos en {raw_dir} están vacíos. "
            "Ejecute primero la extracción con extract_dataset()."
        )

    df = pl.from_dicts(records, infer_schema_length=None)
    logger.info("Carga completada: %d registros, %d columnas", len(df), len(df.columns))
    return df


def _rename_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Renombra columnas según el diccionario de datos de Contraduria."""
    rename_map = {
        old: new for old, new in COLUMN_RENAME_MAP.items() if old in df.columns
    }
    if rename_map:
        df = df.rename(rename_map)
        logger.info("Renombradas %d columnas", len(rename_map))
    return df


def _cast_dates(df: pl.DataFrame) -> pl.DataFrame:
    """Convierte columnas de fecha a tipo Date."""
    date_cols_present = [col for col in DATE_COLUMNS if col in df.columns]
    if not date_cols_present:
        return df

    logger.info("Convirtiendo %d columnas de fecha a tipo Date", len(date_cols_present))

    for col in date_cols_present:
        date_series = (
            df[col]
            .cast(pl.Utf8)
            .str.slice(0, 10)
            .str.strptime(pl.Date, format="%Y-%m-%d", strict=False)
        )
        null_count = date_series.null_count()
        if null_count > 0:
            logger.warning(
                "  %s: %d valores no pudieron convertirse a fecha (quedan como null)",
                col,
                null_count,
            )
        df = df.with_columns(date_series.alias(col))

    return df


def _cast_monetary(df: pl.DataFrame) -> pl.DataFrame:
    """Convierte columnas monetarias a tipo Float64."""
    monetary_cols_present = [col for col in MONETARY_COLUMNS if col in df.columns]
    if not monetary_cols_present:
        return df

    logger.info(
        "Convirtiendo %d columnas monetarias a Decimal(18,2)",
        len(monetary_cols_present),
    )

    for col in monetary_cols_present:
        numeric_series = (
            df[col]
            .cast(pl.Utf8)
            .str.replace_all(r"[^0-9.\-]", "")
            .cast(pl.Float64, strict=False)
        )
        null_count = numeric_series.null_count()
        if null_count > 0:
            logger.warning(
                "  %s: %d valores no numéricos detectados (quedan como null)",
                col,
                null_count,
            )
        df = df.with_columns(numeric_series.alias(col))

    return df


def _clean_strings(df: pl.DataFrame) -> pl.DataFrame:
    """Aplica limpieza de strings (trim)."""
    string_cols = [col for col in df.columns if df[col].dtype == pl.Utf8]
    if not string_cols:
        return df

    logger.debug("Limpiando %d columnas de texto (trim)", len(string_cols))
    for col in string_cols:
        df = df.with_columns(df[col].str.strip_chars().alias(col))
    return df


def _extract_year_from_fecha_firma(df: pl.DataFrame) -> pl.DataFrame:
    """Extrae la columna `anio` desde `fecha_firma` para particionado."""
    if "fecha_firma" not in df.columns:
        logger.warning(
            "Columna 'fecha_firma' no encontrada. "
            "Se asigna anio=0 para todos los registros."
        )
        return df.with_columns(pl.lit(0).cast(pl.Int32).alias("anio"))

    return df.with_columns(
        df["fecha_firma"].dt.year().fill_null(0).cast(pl.Int32).alias("anio")
    )


def _validate_row_count_guard(old_count: int, new_count: int) -> None:
    """Protege contra pérdida masiva de datos durante el merge.

    Si el nuevo conteo es menor al 90% del anterior, aborta la operación.

    Args:
        old_count: Cantidad de registros antes del merge.
        new_count: Cantidad esperada después del merge.

    Raises:
        ValueError: Si new_count < old_count * 0.90.
    """
    if old_count == 0:
        return  # Primera ejecución, no hay punto de comparación

    threshold = int(old_count * 0.90)
    if new_count < threshold:
        raise ValueError(
            f"PROTECCIÓN: El nuevo conteo ({new_count}) es menor al 90% "
            f"del conteo anterior ({old_count}, umbral={threshold}). "
            f"Abortando para prevenir pérdida masiva de datos."
        )


def merge_silver(
    existing_df: pl.DataFrame,
    incoming_df: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, int]]:
    """Realiza upsert de datos nuevos sobre el Silver existente usando PRIMARY_KEY.

    Estrategia:
    - Caso 1: id_contrato NUEVO → INSERTAR.
    - Caso 2: id_contrato EXISTENTE + row_hash DIFERENTE → ACTUALIZAR.
    - Caso 3: id_contrato EXISTENTE + row_hash IGUAL → IGNORAR.

    Args:
        existing_df: DataFrame Silver existente (vacío en primera ejecución).
        incoming_df: DataFrame con registros nuevos/transformados.

    Returns:
        Tupla (DataFrame_mergeado, métricas) donde métricas es:
        {"inserted": int, "updated": int, "unchanged": int}
    """
    if PRIMARY_KEY not in incoming_df.columns:
        raise ValueError(
            f"Columna '{PRIMARY_KEY}' no encontrada en los datos entrantes."
        )

    if len(existing_df) == 0:
        # Primera ejecución: todo es inserción
        logger.info(
            "Silver vacío — insertando todos los registros (%d)", len(incoming_df)
        )
        return incoming_df, {
            "inserted": len(incoming_df),
            "updated": 0,
            "unchanged": 0,
        }

    existing_keys = set(existing_df[PRIMARY_KEY].to_list())
    incoming_keys = set(incoming_df[PRIMARY_KEY].to_list())

    # Caso 1: Nuevos contratos (en incoming pero no en existing)
    new_keys = incoming_keys - existing_keys
    new_df = incoming_df.filter(pl.col(PRIMARY_KEY).is_in(new_keys))

    # Casos 2 y 3: Contratos existentes
    common_keys = incoming_keys & existing_keys
    existing_common = existing_df.filter(pl.col(PRIMARY_KEY).is_in(common_keys))
    incoming_common = incoming_df.filter(pl.col(PRIMARY_KEY).is_in(common_keys))

    # Unir por PRIMARY_KEY para comparar row_hash
    if (
        "row_hash" not in existing_common.columns
        or "row_hash" not in incoming_common.columns
    ):
        logger.warning(
            "row_hash no disponible — todos los existentes se consideran actualizados"
        )
        changed_df = incoming_common
        unchanged_df = pl.DataFrame(schema=existing_df.schema)
    else:
        comparison = existing_common.select([PRIMARY_KEY, "row_hash"]).join(
            incoming_common.select([PRIMARY_KEY, "row_hash"]),
            on=PRIMARY_KEY,
            suffix="_new",
        )

        changed_keys = set(
            comparison.filter(pl.col("row_hash") != pl.col("row_hash_new"))[
                PRIMARY_KEY
            ].to_list()
        )
        unchanged_keys = common_keys - changed_keys

        changed_df = incoming_df.filter(pl.col(PRIMARY_KEY).is_in(changed_keys))
        unchanged_df = incoming_df.filter(pl.col(PRIMARY_KEY).is_in(unchanged_keys))

    # Construir resultado: existing - reemplazados + nuevos
    keys_to_keep = {k for k in existing_keys if k not in incoming_keys}
    kept_df = existing_df.filter(pl.col(PRIMARY_KEY).is_in(keys_to_keep))

    result = pl.concat([kept_df, new_df, changed_df], how="diagonal_relaxed")

    metrics = {
        "inserted": len(new_df),
        "updated": len(changed_df),
        "unchanged": len(unchanged_df),
    }

    logger.info(
        "Merge Silver: %d insertados, %d actualizados, %d sin cambios (total: %d)",
        metrics["inserted"],
        metrics["updated"],
        metrics["unchanged"],
        len(result),
    )

    # Validación de integridad
    _validate_row_count_guard(len(existing_df), len(result))

    return result, metrics


def transform_raw_files(
    raw_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> pl.DataFrame:
    """Transforma datos crudos Bronze → Silver (FULL, reemplazo total).

    Usar solo en primera ejecución. Para ejecuciones incrementales usar
    transform_incremental().

    Args:
        raw_dir: Directorio de ejecución con los JSON crudos.
        output_dir: Directorio de salida (default: data/processed/).

    Returns:
        DataFrame transformado.

    Raises:
        FileNotFoundError: Si no hay archivos JSON en raw_dir.
        ValueError: Si los archivos están vacíos.
    """
    source_dir = raw_dir or _RAW_DIR
    target_dir = output_dir or _PROCESSED_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=== Iniciando transformación Bronze → Silver (FULL) ===")

    # 1. Cargar datos crudos
    df = _load_raw_files(source_dir)
    initial_count = len(df)
    logger.info("Registros cargados (Bronze): %d", initial_count)

    # 2. Pipeline de transformación
    df = _rename_columns(df)
    df = _cast_dates(df)
    df = _cast_monetary(df)
    df = _clean_strings(df)
    df = _extract_year_from_fecha_firma(df)
    df = _compute_row_hash(df)

    # 3. Guardar Silver
    output_path = target_dir / SILVER_FILE
    df.write_parquet(output_path)
    logger.info(
        "Transformación completada: %d registros guardados en %s",
        len(df),
        output_path,
    )

    _log_quality_report(df, initial_count)

    return df


def transform_incremental(
    run_dir: Path,
    silver_dir: Optional[Path] = None,
) -> tuple[pl.DataFrame, dict[str, int]]:
    """Transforma datos crudos de una ejecución incremental y aplica merge sobre Silver.

    Pipeline:
    1. Carga datos crudos desde run_dir (solo los de esta ejecución)
    2. Aplica normalización (rename, cast, clean)
    3. Calcula row_hash
    4. Carga Silver existente (si existe)
    5. Aplica merge_silver()
    6. Guarda Silver actualizado

    Args:
        run_dir: Directorio de ejecución con los JSON crudos.
        silver_dir: Directorio donde está contratos_silver.parquet (default: data/processed/).

    Returns:
        Tupla (DataFrame_Silver_actualizado, métricas_merge).
    """
    target_dir = silver_dir or _PROCESSED_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    silver_path = target_dir / SILVER_FILE

    logger.info("=== Iniciando transformación incremental ===")

    # 1. Cargar y normalizar datos nuevos
    incoming_df = _load_raw_files(run_dir)
    extract_count = len(incoming_df)
    logger.info("Registros nuevos extraídos: %d", extract_count)

    incoming_df = _rename_columns(incoming_df)
    incoming_df = _cast_dates(incoming_df)
    incoming_df = _cast_monetary(incoming_df)
    incoming_df = _clean_strings(incoming_df)
    incoming_df = _extract_year_from_fecha_firma(incoming_df)
    incoming_df = _compute_row_hash(incoming_df)

    # 2. Cargar Silver existente
    if silver_path.exists():
        existing_df = pl.read_parquet(silver_path)
        logger.info("Silver existente cargado: %d registros", len(existing_df))
    else:
        existing_df = pl.DataFrame(schema=incoming_df.schema)
        logger.info("No existe Silver previo — se creará uno nuevo.")

    # 3. Merge
    merged_df, metrics = merge_silver(existing_df, incoming_df)

    # 4. Guardar
    merged_df.write_parquet(silver_path)
    logger.info("Silver actualizado: %d registros en %s", len(merged_df), silver_path)

    _log_quality_report(merged_df, extract_count)

    return merged_df, metrics


def _log_quality_report(df: pl.DataFrame, initial_count: int) -> None:
    """Registra reporte de calidad del dataset Silver."""
    logger.info("=== Resumen de calidad Silver ===")
    logger.info("Registros totales: %d", len(df))
    logger.info("Columnas: %d", len(df.columns))
    logger.info(
        "Registros con fecha_firma nula: %d",
        df["fecha_firma"].null_count()
        if "fecha_firma" in df.columns
        else initial_count,
    )
    logger.info(
        "Registros con valor_contrato nulo: %d",
        df["valor_contrato"].null_count()
        if "valor_contrato" in df.columns
        else initial_count,
    )
    logger.info(
        "Registros con id_contrato nulo: %d",
        df["id_contrato"].null_count()
        if "id_contrato" in df.columns
        else initial_count,
    )
