import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { useTopContractors } from "@/hooks/useTopContractors";
import { createTestQueryClient } from "../../utils/createTestQueryClient";

const wrapper = ({ children }: { children: ReactNode }) =>
  createElement(QueryClientProvider, { client: createTestQueryClient() }, children);

describe("useTopContractors", () => {
  it("returns contractors list", async () => {
    const { result } = renderHook(() => useTopContractors(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items.length).toBeGreaterThan(0);
  });
});