import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { useKPI } from "@/hooks/useKPI";
import { createTestQueryClient } from "../../utils/createTestQueryClient";

const wrapper = ({ children }: { children: ReactNode }) =>
  createElement(QueryClientProvider, { client: createTestQueryClient() }, children);

describe("useKPI", () => {
  it("returns KPIs on success", async () => {
    const { result } = renderHook(() => useKPI(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.total_contratos).toBe(12847);
    expect(result.current.data?.entidades).toBe(1245);
    expect(result.current.data?.contratistas_unicos).toBe(8923);
  });
});