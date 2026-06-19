# Testing — Contraduría Frontend

## Estructura

```
frontend/
├── tests/
│   ├── unit/                      # Unit tests (Vitest)
│   │   ├── lib/utils.test.ts      # Utility functions (100% coverage)
│   │   └── components/            # UI component tests
│   │       └── Button.test.tsx
│   ├── integration/               # Integration tests (Vitest + RTL)
│   ├── e2e/                       # E2E tests (Playwright)
│   ├── fixtures/                  # Datos de prueba tipados
│   │   ├── stats.fixture.ts       # /stats response
│   │   ├── contracts.fixture.ts   # /contratos response
│   │   ├── contract-detail.fixture.ts  # /contratos/:id response
│   │   ├── entities.fixture.ts    # /entidades response
│   │   └── suppliers.fixture.ts   # /proveedores response
│   ├── mocks/                     # MSW (Mock Service Worker)
│   │   ├── handlers.ts            # 10 API handlers
│   │   └── server.ts              # MSW server setup
│   ├── utils/                     # Test utilities
│   │   ├── renderWithProviders.tsx  # Wrapper (QueryClient + Router)
│   │   └── createTestQueryClient.ts # QueryClient sin retries
│   └── setupTests.ts              # Jest-DOM + MSW lifecycle
│
├── vitest.config.ts               # Vitest configuration
├── playwright.config.ts           # Playwright configuration
└── .github/workflows/test.yml     # CI pipeline
```

## Comandos

```bash
# Unit + Integration tests (CI mode)
npm test

# Watch mode (desarrollo)
npm run test:watch

# Coverage report
npm run test:coverage

# UI mode (interactivo)
npm run test:ui

# E2E tests (headless)
npm run test:e2e

# E2E tests (UI mode)
npm run test:e2e:ui
```

## Tecnologías

| Capa | Tecnología |
|------|-----------|
| Test Runner | Vitest |
| DOM Environment | jsdom |
| React Testing | @testing-library/react |
| User Events | @testing-library/user-event |
| Matchers | @testing-library/jest-dom |
| Mock API | MSW (Mock Service Worker) |
| Coverage | V8 |
| E2E | Playwright |

## Testing Pyramid

```
                 E2E
               Playwright
                    ▲
             Integration
           React Testing Library
                    ▲
                 Unit
                 Vitest
```

## Coverage Thresholds

| Métrica | Mínimo |
|---------|--------|
| Statements | 80% |
| Branches | 75% |
| Functions | 80% |
| Lines | 80% |

## Fixtures

Los fixtures simulan respuestas reales de la API SECOP II:

```typescript
import { statsFixture } from "../fixtures/stats.fixture";

// statsFixture contiene:
// - total_contratos: 12847
// - valor_total_contratado: 87.3B COP
// - total_entidades: 1245
```

## MSW Handlers

La mock API intercepta todas las llamadas HTTP:

```typescript
// Los handlers definidos en tests/mocks/server.ts
// interceptan automáticamente:
// GET  /api/stats          → 200 + statsFixture
// GET  /api/contratos      → 200 + contractsFixture
// GET  /api/contratos/:id  → 200 + contractDetailFixture
// GET  /api/entidades      → 200 + entitiesFixture
// GET  /api/error-test     → 500 (para tests de error)
```

## renderWithProviders

Wrapper que incluye todos los providers necesarios:

```tsx
import { renderWithProviders } from "../utils/renderWithProviders";

const { getByText } = renderWithProviders(<MyComponent />, {
  initialRoute: "/contratos?anio=2025",
});
```

## Ejemplo: Test de un hook

```typescript
import { renderHook, waitFor } from "@testing-library/react";
import { useStats } from "@/hooks";
import { createTestQueryClient } from "../utils/createTestQueryClient";

it("fetches stats", async () => {
  const queryClient = createTestQueryClient();
  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  const { result } = renderHook(() => useStats(), { wrapper });
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data.total_contratos).toBe(12847);
});
```

## Ejemplo: Test de integración

```tsx
import { renderWithProviders } from "../utils/renderWithProviders";
import DashboardPage from "@/app/dashboard";

it("renders KPIs", async () => {
  const { findByText } = renderWithProviders(<DashboardPage />);
  expect(await findByText("$ 87.3B")).toBeInTheDocument();
  expect(await findByText("12.847")).toBeInTheDocument();
});
```

## CI Pipeline (GitHub Actions)

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm test
      - run: npm run test:coverage
      - run: npm run build
      - run: npx playwright install --with-deps chromium
      - run: npm run test:e2e
```

## E2E con Playwright

Los tests E2E se ejecutan contra el build de producción:

```bash
npm run build
npm run preview &  # Inicia servidor en localhost:4173
npm run test:e2e    # Ejecuta Playwright contra el preview
```

Los tests E2E no hacen llamadas reales al backend — usan MSW con los mismos fixtures.