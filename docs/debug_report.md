# Debug Report — Contraduría Sprint 5

## Fecha
2026-06-18

## Resumen de ejecución
- **Backend:** FastAPI en `localhost:8000` ✅
- **Frontend:** Vite en `localhost:5173` ✅  
- **Proxy Vite → FastAPI:** `/api/*` → `localhost:8000` ✅
- **API Docs:** `http://localhost:8000/docs` (Swagger UI) ✅

---

## Issues encontrados y corregidos

### 1. 🔴 Router de analytics NO registrado en main.py

**Severidad:** Critical  
**Archivo:** `backend/app/main.py`  
**Síntoma:** Endpoints `/analytics/kpi`, `/analytics/top-contractors`, `/analytics/by-locality`, `/analytics/risk-contracts` devolvían 404  
**Root cause:** El archivo `backend/app/api/analytics.py` existía pero su router nunca fue importado ni registrado en `main.py`  
**Fix:** Agregado `from app.api import analytics` y `app.include_router(analytics.router)`  
**Status:** ✅ Fixed

---

### 2. 🔴 Import incorrecto de ErrorResponse en analytics.py

**Severidad:** Critical  
**Archivo:** `backend/app/api/analytics.py`  
**Síntoma:** `ImportError: cannot import name 'ErrorResponse' from 'app.schemas.contracts'`  
**Root cause:** `ErrorResponse` está definido en `app.schemas.common`, no en `app.schemas.contracts`  
**Fix:** Cambiado `from app.schemas.contracts import ErrorResponse` → `from app.schemas.common import ErrorResponse`  
**Status:** ✅ Fixed

---

### 3. 🔴 DuckDB configurado como read_only=True con memoria

**Severidad:** High  
**Archivo:** `backend/app/core/config.py`  
**Síntoma:** `CatalogException: Cannot launch in-memory database in read-only mode!`  
**Root cause:** `duckdb_read_only=True` es incompatible con `database=":memory:"`  
**Fix:** Cambiado `duckdb_read_only: bool = False` como default  
**Status:** ✅ Fixed

---

### 4. 🟡 Frontend tiene su propio proxy correcto

**Severidad:** Info  
**Archivo:** `frontend/vite.config.ts`  
**Verificación:** Proxy `/api` → `http://localhost:8000` con `changeOrigin: true` y `rewrite` quitando `/api`  
**Status:** ✅ Funcionando correctamente

---

### 5. 🟡 Sin datos Parquet (esperado en desarrollo)

**Severidad:** Low  
**Síntoma:** Endpoints devuelven 500 con "vista contratos no disponible"  
**Root cause:** No se ha ejecutado el pipeline ETL. DuckDB no tiene tablas.  
**Fix (futuro):** Ejecutar `cd backend/etl && uv run python etl_runner.py` o similar  
**Status:** ⚠️ Pendiente — Sprint 5 ETL

---

### 6. 🟢 CORS configurado correctamente

**Archivo:** `backend/app/main.py`  
**Configuración:** `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]`  
**Status:** ✅

---

## Pruebas de endpoints (via proxy Vite)

| Endpoint | Status | Response |
|----------|--------|----------|
| `GET /api/health` | 200 | `{"status":"ok","version":"0.1.0"}` |
| `GET /api/docs` | 200 | Swagger UI |
| `GET /api/contratos?page_size=1` | 500 | DuckDB sin datos |
| `GET /api/analytics/kpi` | 500 | DuckDB sin datos |
| `GET /` (Vite) | 200 | React app cargada |