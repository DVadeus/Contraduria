import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppErrorBoundary } from "@/components/error/AppErrorBoundary";

function ThrowError({ shouldThrow = false }: { shouldThrow?: boolean }) {
  if (shouldThrow) throw new Error("Test error");
  return <p>All good</p>;
}

describe("AppErrorBoundary", () => {
  it("renders children when no error", () => {
    render(
      <AppErrorBoundary>
        <ThrowError />
      </AppErrorBoundary>,
    );
    expect(screen.getByText("All good")).toBeInTheDocument();
  });

  it("shows fallback on error", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <AppErrorBoundary>
        <ThrowError shouldThrow />
      </AppErrorBoundary>,
    );
    expect(screen.getByText("Algo salió mal")).toBeInTheDocument();
    expect(screen.getByText("Reintentar")).toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it("shows retry button", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <AppErrorBoundary>
        <ThrowError shouldThrow />
      </AppErrorBoundary>,
    );
    expect(screen.getByRole("button", { name: /reintentar/i })).toBeInTheDocument();
    vi.restoreAllMocks();
  });
});