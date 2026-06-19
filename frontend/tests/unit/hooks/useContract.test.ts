import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { useContract } from "@/hooks/useContract";
import { createTestQueryClient } from "../../utils/createTestQueryClient";

const wrapper = ({ children }: { children: ReactNode }) =>
  createElement(QueryClientProvider, { client: createTestQueryClient() }, children);

describe("useContract", () => {
  it("fetches contract by id", async () => {
    const { result } = renderHook(() => useContract("LP-EMB-002-2026"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.nombre_entidad).toBe("Empresa Metro de Bogotá");
    expect(result.current.data?.valor_contrato).toBe(11_250_000_000);
  });

  it("handles not found", async () => {
    const { result } = renderHook(() => useContract("not-found"), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });

  it("does not fetch without id", () => {
    const { result } = renderHook(() => useContract(undefined), { wrapper });
    expect(result.current.isLoading).toBe(false);
  });
});