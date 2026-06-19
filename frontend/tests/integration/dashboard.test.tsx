import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../utils/renderWithProviders";
import DashboardPage from "@/app/dashboard";

describe("Dashboard", () => {
  it("renders KPI section", async () => {
    renderWithProviders(<DashboardPage />);
    expect(await screen.findByText("Analiza", { exact: false })).toBeInTheDocument();
    expect(await screen.findByText("Total Contratado")).toBeInTheDocument();
    expect(screen.getByText("Contratos Activos")).toBeInTheDocument();
    expect(screen.getByText("Contratistas Únicos")).toBeInTheDocument();
  });

  it("renders chart sections", async () => {
    renderWithProviders(<DashboardPage />);
    expect(await screen.findByText("Top Entidades por Valor")).toBeInTheDocument();
    expect(screen.getByText("Top Proveedores")).toBeInTheDocument();
    expect(screen.getByText("Modalidades de Contratación")).toBeInTheDocument();
    expect(screen.getByText("Tendencia Anual")).toBeInTheDocument();
  });

  it("renders risk alerts panel", async () => {
    renderWithProviders(<DashboardPage />);
    expect(await screen.findByText("Alertas de Riesgo")).toBeInTheDocument();
  });
});