# Evaluación del Pipeline ETL — Contraduria

> **Fecha:** 2026-06-19
> **Versión:** 0.1.0
> **Dataset:** SECOP II — `jbjy-vk9h` (Socrata Open Data API)

---

## Resumen Ejecutivo

El pipeline ETL de Contraduria descarga, transforma y carga el dataset completo de contratación
pública SECOP II desde `datos.gov.co`. Sigue el patrón Bronze → Silver → Gold con herramientas
optimizadas (HTTPX, Polars, DuckDB, Parquet).

| Métrica | Estimación |
|---|---|
| Registros descargados | **~1.5 millones** |
| Tiempo total (FULL LOAD) | **8–22 minutos** |
| Espacio en disco | **5–10 GB** |
| Archivos Parquet Gold | **~400 MB – 1.2 GB** |
| Páginas HTTP | **~31 páginas** |
| Riesgo de rate limiting | **Bajo** (con token o sin él) |

---

## 1. Arquitectura del Pipeline

```
SECOP II (Socrata)
        │
        ▼
     Bronze (data/raw/<run_id>/)
  ~31 archivos JSON crudos por página
        │
        ▼
     Silver (data/processed/contratos_silver.parquet)
  Tipos normalizados, columnas renombradas, row_hash SHA256
        │
        ▼
      Gold (data/parquet/contratos_{year}.parquet)
  Particionado por año, registrado en DuckDB
        │
        ▼
   Data Marts (vistas DuckDB)
  Agregaciones analíticas, KPIs
```

### Módulos

| Módulo | Archivo | Líneas | Responsabilidad |
|---|---|---|---|
| Extract | `etl/extract/socrata_extractor.py` | 333 | Descarga paginada con HTTPX + HTTP/2 |
| Transform | `etl/transform/socrata_transformer.py` | 558 | Normalización con Polars, merge incremental |
| Load | `etl/load/parquet_loader.py` | 274 | Particionado por año, registro DuckDB |
| Orchestrator | `etl/orchestrator.py` | 388 | Coordinación del pipeline, metadata, marts |
| Metadata | `etl/metadata.py` | 159 | Estado ETL, historial JSONL |

---

## 2. Cantidad de Registros Descargados

### Estimación: ~1,523,400 registros

**Evidencia:**

1. El propio `metadata.py` usa `last_silver_record_count: 1523400` como valor de ejemplo en su docstring, indicando que el equipo espera ~1.52M registros.
2. El dataset SECOP II en `datos.gov.co` históricamente contiene entre 1.4 y 2.0 millones de contratos.
3. Con `$limit=50000`, se requieren **~31 páginas** para descargar 1.52M registros.

### Distribución estimada por año

| Año | Registros estimados | % del total |
|---|---|---|
| 2021 | 200,000 – 300,000 | ~16% |
| 2022 | 250,000 – 350,000 | ~20% |
| 2023 | 280,000 – 380,000 | ~22% |
| 2024 | 280,000 – 400,000 | ~23% |
| 2025 | 200,000 – 300,000 | ~16% |
| 2026 | 50,000 – 100,000 | ~4% |

---

## 3. Tiempo Estimado de Ejecución

### Desglose por etapa

| Etapa | Duración estimada | Operaciones |
|---|---|---|
| **1. Extract (Bronze)** | **5–15 min** | 31 peticiones HTTP a `datos.gov.co`, timeout 60s c/u, 3 reintentos con backoff exponencial (2s → 4s → 8s). Latencia típica desde Colombia: 5–15s por página. Desde fuera de CO: 15–30s. |
| **2. Transform (Silver)** | **1–3 min** | Polars: carga de ~31 JSONs (~4–8 GB en memoria), rename 70+ columnas, cast de fechas (3 columnas), cast de valores monetarios (10 columnas), trim de strings (~80 columnas), compute SHA256 row_hash por fila, extraer año desde `fecha_firma`. |
| **3. Load (Gold)** | **1–2 min** | Particionado Polars por año (6 particiones), escritura Parquet con compresión Snappy. DuckDB registra vista `contratos` sobre todos los archivos Gold. |
| **4. Build Marts** | **30–90 s** | DuckDB: agregaciones analíticas (KPIs, top contractors, risk scoring). |
| **Total** | **8–22 min** | Dominado por latencia de red a Socrata. |

### Factores que afectan el tiempo

| Factor | Impacto |
|---|---|
| Ubicación geográfica | Fuera de Colombia: +5–15 min adicionales |
| Token Socrata (`SOCRATA_APP_TOKEN`) | Sin impacto significativo en tiempo (31 páginas es poco) |
| Recursos de la máquina | Mínimo 8 GB RAM recomendado para Silver |
| Conexión a internet | Banda ancha estándar (>10 Mbps) es suficiente |

---

## 4. Espacio en Disco Requerido

### Por capa

| Capa | Formato | Archivos | Tamaño estimado | Persistencia |
|---|---|---|---|---|
| **Bronze** | JSON (sin comprimir) | ~31 archivos `.json` | **4–8 GB** | Temporal (por ejecución) |
| **Silver** | Parquet (Snappy) | 1 archivo `contratos_silver.parquet` | **400 MB – 1.2 GB** | Conservar |
| **Gold** | Parquet (Snappy) | 6 archivos `contratos_{year}.parquet` | **400 MB – 1.2 GB** | Conservar |
| **Metadata** | JSON + JSONL | 2 archivos pequeños | **< 10 KB** | Conservar |
| **Total** | | | **5–10 GB** | |

### Relación de compresión

| Origen | Tamaño por registro | Total 1.5M registros |
|---|---|---|
| JSON crudo (Bronze) | ~3–5 KB | ~4–8 GB |
| Parquet Snappy (Silver/Gold) | ~300–800 bytes | ~400 MB – 1.2 GB |
| **Ratio de compresión** | | **5× – 10×** |

### Tamaño esperado por archivo Parquet Gold

| Archivo | Tamaño estimado |
|---|---|
| `contratos_2021.parquet` | 50–150 MB |
| `contratos_2022.parquet` | 80–200 MB |
| `contratos_2023.parquet` | 100–250 MB |
| `contratos_2024.parquet` | 120–300 MB |
| `contratos_2025.parquet` | 80–200 MB |
| `contratos_2026.parquet` | 30–100 MB |

---

## 5. Riesgos de Rate Limiting de Socrata

### Evaluación general: **Bajo riesgo**

**Contexto:**
- Socrata limita peticiones a **1,000 por hora** sin App Token, o **50,000 por día** con App Token.
- El pipeline solo hace **~31 peticiones** (una por página de 50K registros), muy por debajo de cualquier límite.
- Incluso sin token, 31 peticiones en ~15 minutos (~124 req/hora) está dentro de los límites normales.

### Matriz de riesgos

| Riesgo | Severidad | Probabilidad | Mitigación implementada |
|---|---|---|---|
| **Rate limit sin App Token** | Bajo | Baja | El código soporta `SOCRATA_APP_TOKEN` vía variable de entorno (línea 48 de `socrata_extractor.py`). |
| **Timeout de red** | Medio | Media | Timeout configurable (default 60s). 3 reintentos con backoff exponencial: 2s → 4s → 8s (`DEFAULT_RETRY_BACKOFF`). |
| **Páginas vacías consecutivas** | Bajo | Baja | `MAX_DUPLICATE_PAGES = 3`: el extractor aborta tras 3 páginas vacías, asumiendo fin del dataset. |
| **Respuesta no-JSON** | Bajo | Baja | Validación `isinstance(data, list)` en `fetch_page()`. Si Socrata devuelve error/HTML, se registra warning y se retorna `[]`. |
| **Datos malformados** | Medio | Media | Cast con `strict=False`: fechas no parseables → null; valores monetarios no numéricos → null. Ambos con warning de cuántos valores fallaron. |
| **Pérdida masiva en merge** | Bajo | Baja | `_validate_row_count_guard()`: aborta si nuevo conteo < 90% del anterior (línea 316 del transformer). |
| **API caída / mantenimiento** | Alto | Baja | Sin mitigación automática. El pipeline fallará y lo registrará en `run_history.jsonl` con status `"failed"`. |
| **Lentitud extrema (>30s por página)** | Medio | Media | Timeout de 60s por página. Si todas las páginas son lentas, el extract puede tomar >30 min. No hay timeout global del pipeline. |

### Recomendaciones

1. **Obtener un App Token de Socrata** (gratuito en `datos.gov.co` → perfil → API Key) y configurarlo como variable de entorno `SOCRATA_APP_TOKEN`. Aunque no es crítico para 31 páginas, habilita mayor throughput si se necesitan filtros adicionales.
2. **Ejecutar el ETL desde una máquina en Colombia** para minimizar latencia de red.
3. **Monitorear la primera ejecución** para calibrar tiempos reales y ajustar timeouts si es necesario.
4. **Considerar un timeout global** del pipeline (ej. 45 min) para evitar ejecuciones colgadas en caso de degradación extrema de la API.
5. **Programar ejecuciones en horarios de baja carga** en `datos.gov.co` (madrugada hora Colombia, UTC-5).

---

## 6. Parámetros de Configuración

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `DEFAULT_BASE_URL` | `https://www.datos.gov.co/resource/jbjy-vk9h.json` | Endpoint Socrata |
| `DEFAULT_LIMIT` | `50000` | Tamaño de página (máx sin App Token) |
| `DEFAULT_TIMEOUT` | `60.0` s | Timeout HTTP por página |
| `DEFAULT_MAX_RETRIES` | `3` | Reintentos por página |
| `DEFAULT_RETRY_BACKOFF` | `2.0` s | Base backoff exponencial |
| `LOOKBACK_DAYS` | `7` | Días de lookback en incremental |
| `WATERMARK_COLUMN` | `ultima_actualizacion` | Columna para incremental |
| `PRIMARY_KEY` | `id_contrato` | Clave primaria para merge/upsert |
| `SILVER_FILE` | `contratos_silver.parquet` | Archivo Silver unificado |
| `GOLD_PATTERN` | `contratos_{year}.parquet` | Patrón archivos Gold |

---

## 7. Requisitos de Sistema

| Recurso | Mínimo | Recomendado |
|---|---|---|
| **RAM** | 8 GB | 16 GB |
| **Disco** | 12 GB libres | 20 GB libres |
| **CPU** | 2 cores | 4+ cores |
| **Red** | >5 Mbps | >20 Mbps |
| **Python** | ≥3.12 | ≥3.13 |
| **Dependencias** | `uv sync` en `backend/` | — |

---

## 8. Modos de Ejecución

### FULL LOAD (primera ejecución)

```bash
cd backend
uv run python -m etl.orchestrator
```

- Descarga el dataset completo (~1.5M registros).
- Genera todos los archivos Bronze, Silver, Gold.
- Construye todos los Data Marts.
- Crea `etl_state.json` con watermark inicial.

### INCREMENTAL (ejecuciones posteriores)

- Se activa automáticamente si `etl_state.json` existe.
- Descarga solo registros nuevos/modificados desde `last_watermark - 7 días`.
- Aplica merge por `id_contrato` + `row_hash` para detectar cambios reales.
- Solo actualiza particiones Gold de años afectados.
- Solo reconstruye Data Marts de años afectados.

### Forzar FULL LOAD

```bash
uv run python -c "from etl.orchestrator import run_etl; run_etl(force_full=True)"
```

---

## 9. Validaciones de Integridad

| Validación | Dónde | Qué hace |
|---|---|---|
| **Páginas vacías** | Extract | Aborta tras 3 páginas vacías consecutivas |
| **Tipos de datos** | Transform | Cast con `strict=False`, registra nulls como warning |
| **Unicidad de PK** | Transform | `merge_silver()` usa `id_contrato` para upsert |
| **Detección de cambios** | Transform | `row_hash` SHA256 para skip de filas sin cambios |
| **Pérdida masiva** | Transform | `_validate_row_count_guard()`: aborta si < 90% |
| **Años afectados** | Load | Solo actualiza particiones con datos modificados |
| **Conteo Gold** | Load | `SELECT COUNT(*) FROM contratos` post-carga |
| **Registro de fallos** | Orchestrator | `run_history.jsonl` con status `"failed"` |

---

## 10. Conclusión

El pipeline ETL de Contraduria está bien diseñado para su propósito:

- **Eficiente:** ~1.5M registros en <22 minutos usando herramientas optimizadas.
- **Robusto:** Reintentos, validaciones de integridad, guardrails contra pérdida de datos.
- **Incremental:** Soporta cargas incrementales con detección de cambios por hash.
- **Bajo riesgo:** Solo 31 peticiones HTTP, muy por debajo de cualquier rate limit de Socrata.

El principal punto de atención es la **latencia de red hacia `datos.gov.co`**, que domina el tiempo total de ejecución. Para entornos de desarrollo local en Colombia, el tiempo estimado de 8–15 minutos es realista. Desde fuera de Colombia, puede extenderse a 20–30 minutos.