import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useStats } from "@/hooks/useStats";
import { createTestQueryClient } from "../../utils/createTestQueryClient";
import { createElement, type ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";

function wrapper({ children }: { children: ReactNode }) {
  return createElement(
    QueryClientProvider,
    { client: createTestQueryClient() },
    children,
  );
}

describe("useStats", () => {
  const setup = () => renderHook(() => useStats(), { wrapper });

  it("enters loading state initially", () => {
    const { result } = setup();
    expect(result.current.isLoading).toBe(true);
  });

  it("returns stats data on success", async () => {
    const { result } = setup();
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeDefined();
    expect(result.current.data?.total_contratos).toBe(12847);
    expect(result.current.data?.total_entidades).toBe(1245);
    expect(result.current.data?.total_proveedores).toBe(8923);
  });

  it("exposes correct KPIs", async () => {
    const { result } = setup();
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const d = result.current.data!;
    expect(d.valor_total_contratado).toBeGreaterThan(0);
    expect(d.anio_desde).toBe(2019);
    expect(d.anio_hasta).toBe(2026);
  });
});