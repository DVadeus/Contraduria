import { render, type RenderOptions } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { type ReactElement, type ReactNode } from "react";
import { createTestQueryClient } from "./createTestQueryClient";

interface ProvidersConfig {
  initialRoute?: string;
}

export function renderWithProviders(
  ui: ReactElement,
  options?: RenderOptions & ProvidersConfig,
) {
  const queryClient = createTestQueryClient();
  const { initialRoute = "/", ...renderOptions } = options ?? {};

  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[initialRoute]}>
          {children}
        </MemoryRouter>
      </QueryClientProvider>
    );
  }

  return {
    queryClient,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  };
}