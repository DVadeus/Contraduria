import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../utils/renderWithProviders";
import ContractsPage from "@/app/contracts";

describe("Contracts Page", () => {
  it("renders table with contracts", async () => {
    const { findByText } = renderWithProviders(<ContractsPage />);
    expect(await findByText("LP-EMB-002-2026")).toBeInTheDocument();
    expect(await findByText("Empresa Metro de Bogotá")).toBeInTheDocument();
  });

  it("shows filter sidebar", async () => {
    renderWithProviders(<ContractsPage />);
    expect(await screen.findByText("Filtros")).toBeInTheDocument();
    expect(screen.getByText("Año")).toBeInTheDocument();
  });

  it("displays pagination", async () => {
    renderWithProviders(<ContractsPage />);
    expect(await screen.findByText(/Página 1/)).toBeInTheDocument();
  });
});