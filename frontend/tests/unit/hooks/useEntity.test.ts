import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { useEntity } from "@/hooks/useEntity";
import { createTestQueryClient } from "../../utils/createTestQueryClient";

const wrapper = ({ children }: { children: ReactNode }) =>
  createElement(QueryClientProvider, { client: createTestQueryClient() }, children);

describe("useEntity", () => {
  it("fetches entity by NIT", async () => {
    const { result } = renderHook(() => useEntity("900.123.456"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.nombre_entidad).toBe("Empresa Metro de Bogotá");
  });

  it("does not fetch without NIT", () => {
    const { result } = renderHook(() => useEntity(undefined), { wrapper });
    expect(result.current.isLoading).toBe(false);
  });
});