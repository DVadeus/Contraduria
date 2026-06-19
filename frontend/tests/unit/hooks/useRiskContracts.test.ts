import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { useRiskContracts } from "@/hooks/useRiskContracts";
import { createTestQueryClient } from "../../utils/createTestQueryClient";

const wrapper = ({ children }: { children: ReactNode }) =>
  createElement(QueryClientProvider, { client: createTestQueryClient() }, children);

describe("useRiskContracts", () => {
  it("returns risk contracts", async () => {
    const { result } = renderHook(() => useRiskContracts(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items.length).toBeGreaterThan(0);
  });
});