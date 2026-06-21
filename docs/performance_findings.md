# Performance Findings — Contraduría Sprint 5

## Bundle Analysis

| Chunk | Size | Gzip | Contenido |
|-------|------|------|-----------|
| `index.html` | 2.23 KB | 0.82 KB | Entry point |
| `index-*.css` | 23.47 KB | 5.51 KB | Tailwind v4 con design tokens |
| `index-*.js` | 311 KB | 99 KB | Shell principal (React, Router, Query) |
| `dashboard-*.js` | 428 KB | 116 KB | Dashboard + Recharts (lazy) |
| `contract-detail-*.js` | 11.4 KB | 2.9 KB | Contract Detail (lazy) |
| `contracts-*.js` | 9.6 KB | 2.9 KB | Contracts Page (lazy) |
| `entities-*.js` | 3.2 KB | 1.2 KB | Entities Page (lazy) |
| `suppliers-*.js` | 3.3 KB | 1.3 KB | Suppliers Page (lazy) |
| `api-*.js` | 11.4 KB | 4.1 KB | API client |
| `proxy-*.js` | 125 KB | 41 KB | React Query + Router shared |

**Total:** ~928 KB minified, ~275 KB gzipped

---

## Lazy Loading Audit

| Ruta | Carga | Efectividad |
|------|-------|-------------|
| `/` | Lazy | ✅ Dashboard (428 KB) solo carga on-demand |
| `/contratos` | Lazy | ✅ 9.6 KB |
| `/contratos/:id` | Lazy | ✅ 11.4 KB |
| `/entidades` | Lazy | ✅ 3.2 KB |
| `/proveedores` | Lazy | ✅ 3.3 KB |

**Todas las rutas usan React.lazy correctamente.**

---

## React Query Configuration

| Setting | Value | Observation |
|---------|-------|-------------|
| `refetchOnWindowFocus` | false | ✅ Evita refetch innecesario |
| `retry` | 1 | ✅ Solo un reintento |
| `staleTime` (hooks) | 2-10 min | ✅ Tiempos razonables |

**Sin problemas de infinite loops o duplicate requests detectados.**

---

## Search & Filter Optimization

### Current State
- **Contract search:** Sin debounce — filtra en cada keystroke via `useSearchParams`
- **Entity search:** Sin debounce — consulta directa a `useEntities(search)`
- **Supplier search:** Sin debounce — consulta directa a `useSuppliers(search)`

### Recommendation
Implementar debounce de 300ms vía `useDebounce` hook personalizado:

```typescript
import { useState, useEffect } from "react";

export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}
```

**Impacto:** Reduce llamadas API innecesarias en búsquedas.

---

## URL State Synchronization

✅ `/contratos` ya sincroniza filtros con query params  
✅ URLs son compartibles: `/contratos?anio=2025&modalidad=Licitación+Pública`  
✅ Refresh, back, forward funcionan correctamente

---

## Accessibility

| Elemento | Status |
|----------|--------|
| Skip to content | ❌ No implementado |
| Landmark roles | ✅ nav, main, aside, footer |
| Keyboard navigation | ✅ Tablas, botones, links |
| aria-labels | ✅ Theme toggle, iconos SVG |
| Focus trap | ✅ En ErrorBoundary dialogs |
| Screen reader | ✅ Labels en botones y inputs |

---

## Error Handling Coverage

| Componente | Estado |
|------------|--------|
| `AppErrorBoundary` | ✅ Captura errores React |
| `ApiErrorState` | ✅ Mensaje + retry |
| `EmptyState` | ✅ Sin resultados |
| `NotFoundState` | ✅ Página 404 |
| `RetryState` | ✅ Botón de reintento |
| Skeletons | ✅ En todas las páginas |

---

## Remaining Technical Debt

| Item | Prioridad | Esfuerzo |
|------|-----------|----------|
| Debounce en búsquedas | Medium | 15 min |
| Skip to content link | Low | 5 min |
| ETL pipeline sin ejecutar | High | Sprint 5 ETL |
| Playwright E2E no ejecutados | Low | `npx playwright install` |
| Recharts v3 migration | Low | Actualizar dependencia |

---

## Recommendations Before Production

1. **Ejecutar ETL pipeline** para poblar DuckDB con datos Parquet
2. **Implementar debounce** en inputs de búsqueda (300ms)
3. **Agregar skip-to-content link** para accesibilidad
4. **`npx playwright install chromium`** para habilitar E2E
5. **Configurar Sentry** para capturar errores en producción (logger.ts ya preparado)