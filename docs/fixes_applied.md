# Fixes Applied — Contraduría Sprint 5

## Archivos Modificados

### 1. `backend/app/main.py`
**Cambio:** Registro del router de analytics  
**Antes:** El router de analytics no estaba importado ni registrado  
**Después:**
```python
from app.api import analytics
# ...
app.include_router(analytics.router)
```
**Impacto:** 4 endpoints ahora accesibles: `/analytics/kpi`, `/analytics/top-contractors`, `/analytics/by-locality`, `/analytics/risk-contracts`

---

### 2. `backend/app/api/analytics.py`
**Cambio:** Corrección de import  
**Antes:** `from app.schemas.contracts import ErrorResponse`  
**Después:** `from app.schemas.common import ErrorResponse`  
**Impacto:** El módulo ahora importa correctamente sin `ImportError`

---

### 3. `backend/app/core/config.py`
**Cambio:** DuckDB read_only default  
**Antes:** `duckdb_read_only: bool = True`  
**Después:** `duckdb_read_only: bool = False`  
**Razón:** `duckdb.connect(database=":memory:", read_only=True)` no es válido en DuckDB. La base de datos en memoria requiere modo lectura/escritura.  
**Impacto:** El backend ahora inicia sin `CatalogException`

---

## Archivos NO Modificados (verificados correctos)

| Archivo | Verificación |
|---------|-------------|
| `frontend/vite.config.ts` | Proxy `/api` → `http://localhost:8000` correcto |
| `frontend/src/lib/api.ts` | API_BASE = `/api` correcto |
| `frontend/package.json` | Todas las dependencias instaladas |
| `backend/app/core/config.py` | CORS allow_origins=["*"] correcto |
| `tests/**` | 79 tests siguen pasando ✅ |

---

## Estado Post-Fix

| Servicio | Puerto | Estado |
|----------|--------|--------|
| FastAPI Backend | 8000 | ✅ Running |
| Vite Frontend | 5173 | ✅ Running |
| Vite Preview | 4173 | ⬜ Off (solo build) |
| Proxy API | 5173→8000 | ✅ Funcionando |
| Swagger UI | 8000/docs | ✅ Accesible |