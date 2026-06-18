"""Extractor Socrata — descarga datos del dataset SECOP II desde datos.gov.co.

Utiliza la Socrata Open Data API (SODA) con paginación obligatoria,
estrategia de reintentos y guardado de respuestas crudas en data/raw/<run_id>/.

Soporta extracción FULL e INCREMENTAL con watermark + lookback.

Reglas ETL aplicadas:
- HTTPX como cliente oficial.
- Paginación con $limit y $offset.
- Timeouts explícitos.
- Reintentos con backoff exponencial.
- Nunca descargar el dataset completo en una sola petición.
- Sin transformaciones — solo extracción cruda.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración por defecto
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "https://www.datos.gov.co/resource/jbjy-vk9h.json"
DEFAULT_LIMIT = 50000  # Máximo permitido por Socrata sin App Token
DEFAULT_TIMEOUT = 60.0  # segundos
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF = 2.0  # segundos base para backoff exponencial

# Watermark incremental
WATERMARK_COLUMN = "ultima_actualizacion"
LOOKBACK_DAYS = 7

# Directorio raíz del proyecto
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_RAW_DIR = _PROJECT_ROOT / "data" / "raw"

# Token Socrata desde variable de entorno
_SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")


def _resolve_raw_dir() -> Path:
    """Resuelve el directorio de datos crudos, permitiendo override por variable de entorno."""
    env_dir = os.getenv("CONTRADURIA_RAW_DIR")
    if env_dir:
        return Path(env_dir)
    return _RAW_DIR


def _build_headers() -> dict[str, str]:
    """Construye los headers HTTP para la petición a Socrata."""
    headers = {
        "Accept": "application/json",
        "User-Agent": "Contraduria/0.1.0 (Portal SECOP Bogota; contacto@contraduria.org)",
    }
    if _SOCRATA_APP_TOKEN:
        headers["X-App-Token"] = _SOCRATA_APP_TOKEN
    return headers


def _create_run_directory(
    parent_dir: Optional[Path] = None, run_id: Optional[str] = None
) -> Path:
    """Crea un directorio único para esta ejecución de extracción.

    Args:
        parent_dir: Directorio padre (default: data/raw/).
        run_id: ID de ejecución (default: generado automáticamente).

    Returns:
        Path al directorio creado.
    """
    base = parent_dir or _resolve_raw_dir()
    if run_id is None:
        now = datetime.now(timezone.utc)
        run_id = now.strftime("run_%Y%m%d_%H%M%S")

    run_dir = base / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Directorio de extracción creado: %s", run_dir)
    return run_dir


def _compute_watermark_lookback(
    watermark_str: Optional[str], lookback_days: int = LOOKBACK_DAYS
) -> Optional[str]:
    """Calcula el watermark con lookback para la extracción incremental.

    Args:
        watermark_str: Watermark anterior en formato ISO (ej. '2026-07-15T00:00:00.000').
        lookback_days: Días hacia atrás para el lookback.

    Returns:
        String con la fecha ajustada en formato ISO, o None si no hay watermark.
    """
    if not watermark_str:
        return None

    try:
        # Extraer solo la parte de fecha (YYYY-MM-DD) ignorando la hora
        date_part = watermark_str[:10]
        watermark_dt = datetime.strptime(date_part, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        adjusted = watermark_dt - timedelta(days=lookback_days)
        return adjusted.strftime("%Y-%m-%dT00:00:00.000")
    except (ValueError, IndexError):
        logger.warning(
            "Watermark inválido: '%s'. Se usará sin lookback.", watermark_str
        )
        return watermark_str


# ---------------------------------------------------------------------------
# Funciones de extracción
# ---------------------------------------------------------------------------


def fetch_page(
    client: httpx.Client,
    url: str,
    params: dict[str, str | int],
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff: float = DEFAULT_RETRY_BACKOFF,
) -> list[dict]:
    """Descarga una página del dataset Socrata con estrategia de reintentos.

    Args:
        client: Cliente HTTPX configurado.
        url: URL base del dataset.
        params: Parámetros de consulta ($limit, $offset, $where, etc.).
        timeout: Timeout en segundos para cada intento.
        max_retries: Número máximo de reintentos.
        backoff: Base en segundos para backoff exponencial.

    Returns:
        Lista de registros (dict) de la página descargada.

    Raises:
        httpx.HTTPError: Si todos los reintentos fallan.
    """
    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            response = client.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                logger.warning(
                    "Socrata no devolvió una lista. Tipo recibido: %s. "
                    "Posible error de autenticación o rate limit.",
                    type(data).__name__,
                )
                return []

            logger.debug(
                "Página descargada: offset=%s, limit=%s, registros=%d",
                params.get("$offset", 0),
                params.get("$limit", 0),
                len(data),
            )
            return data

        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as e:
            last_error = e
            wait = backoff * (2 ** (attempt - 1))
            logger.warning(
                "Intento %d/%d fallido para offset=%s: %s. Reintentando en %.1fs...",
                attempt,
                max_retries,
                params.get("$offset", 0),
                e,
                wait,
            )
            time.sleep(wait)

    raise httpx.HTTPError(
        f"Fallo en los {max_retries} intentos para offset={params.get('$offset', 0)}"
    ) from last_error


def extract_dataset(
    base_url: str = DEFAULT_BASE_URL,
    limit: int = DEFAULT_LIMIT,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff: float = DEFAULT_RETRY_BACKOFF,
    raw_dir: Optional[Path] = None,
    run_id: Optional[str] = None,
    incremental: bool = False,
    watermark: Optional[str] = None,
) -> tuple[int, Path]:
    """Extrae el dataset SECOP II usando paginación con $limit y $offset.

    Soporta dos modos:
    - FULL: descarga el dataset completo (default).
    - INCREMENTAL: descarga solo registros nuevos/modificados desde watermark + lookback.

    Guarda los datos crudos en data/raw/<run_id>/ como archivos JSON (uno por página).

    Args:
        base_url: URL base del dataset Socrata.
        limit: Tamaño de página (batch size). Máximo 50000 sin App Token.
        timeout: Timeout HTTP en segundos.
        max_retries: Reintentos máximos por página.
        backoff: Base en segundos para backoff exponencial.
        raw_dir: Directorio base para guardar datos crudos.
        run_id: ID de ejecución (default: generado automáticamente).
        incremental: Si es True, activa extracción incremental con $where.
        watermark: Watermark anterior para extracción incremental.

    Returns:
        Tupla (total_registros_extraídos, directorio_de_ejecución).

    Raises:
        httpx.HTTPError: Si la extracción falla después de reintentos.
    """
    parent_dir = raw_dir or _resolve_raw_dir()
    output_dir = _create_run_directory(parent_dir, run_id)

    headers = _build_headers()
    total_extracted = 0
    offset = 0
    page_num = 1
    duplicate_pages = 0
    MAX_DUPLICATE_PAGES = 3

    # Construir $where para incremental
    where_clause: Optional[str] = None
    if incremental and watermark:
        watermark_lookback = _compute_watermark_lookback(watermark, LOOKBACK_DAYS)
        if watermark_lookback:
            where_clause = f"{WATERMARK_COLUMN} >= '{watermark_lookback}'"
            logger.info(
                "Extracción INCREMENTAL: $where=%s (watermark original: %s, lookback: %d días)",
                where_clause,
                watermark,
                LOOKBACK_DAYS,
            )

    mode_label = "INCREMENTAL" if where_clause else "FULL"
    logger.info(
        "Iniciando extracción Socrata [%s]: url=%s, limit=%d, timeout=%.0fs, max_retries=%d",
        mode_label,
        base_url,
        limit,
        timeout,
        max_retries,
    )

    with httpx.Client(headers=headers, http2=True) as client:
        while True:
            params: dict[str, str | int] = {
                "$limit": limit,
                "$offset": offset,
            }
            if where_clause:
                params["$where"] = where_clause

            try:
                data = fetch_page(
                    client,
                    base_url,
                    params,
                    timeout=timeout,
                    max_retries=max_retries,
                    backoff=backoff,
                )
            except httpx.HTTPError as e:
                logger.error("Extracción abortada en offset=%d: %s", offset, e)
                raise

            if not data:
                duplicate_pages += 1
                logger.info(
                    "Página %d vacía en offset=%d (%d/%d páginas vacías consecutivas)",
                    page_num,
                    offset,
                    duplicate_pages,
                    MAX_DUPLICATE_PAGES,
                )

                if duplicate_pages >= MAX_DUPLICATE_PAGES:
                    logger.info(
                        "Se detectaron %d páginas vacías consecutivas. "
                        "Se asume fin del dataset.",
                        MAX_DUPLICATE_PAGES,
                    )
                    break

            else:
                duplicate_pages = 0

                # Guardar página cruda como JSON
                page_file = (
                    output_dir
                    / f"socrata_page_{page_num:06d}_offset_{offset:010d}.json"
                )
                with open(page_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)

                total_extracted += len(data)
                logger.info(
                    "Página %d guardada: %s (%d registros, total acumulado: %d)",
                    page_num,
                    page_file.name,
                    len(data),
                    total_extracted,
                )

            offset += limit
            page_num += 1

    logger.info(
        "Extracción [%s] completada: %d registros en %d páginas. Directorio: %s",
        mode_label,
        total_extracted,
        page_num - 1,
        output_dir,
    )
    return total_extracted, output_dir
