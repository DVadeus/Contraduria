import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { useContracts } from "@/hooks/useContracts";
import { createTestQueryClient } from "../../utils/createTestQueryClient";
import type { ContractFilters } from "@/types";

const wrapper = ({ children }: { children: ReactNode }) =>
  createElement(QueryClientProvider, { client: createTestQueryClient() }, children);

describe("useContracts", () => {
  const setup = (filters: ContractFilters = { page: 1, page_size: 50 }) =>
    renderHook(() => useContracts(filters), { wrapper });

  it("loading initially", () => {
    const { result } = setup();
    expect(result.current.isLoading).toBe(true);
  });

  it("returns contracts on success", async () => {
    const { result } = setup();
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items).toBeDefined();
    expect(result.current.data?.items.length).toBeGreaterThan(0);
    expect(result.current.data?.total).toBe(12847);
  });

  it("sends year filter", async () => {
    const { result } = setup({ anio: 2025, page: 1, page_size: 50 });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items).toBeDefined();
  });

  it("sends entity filter", async () => {
    const { result } = setup({ entidad: "Metro", page: 1, page_size: 50 });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});