import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../utils/renderWithProviders";
import SuppliersPage from "@/app/suppliers";

describe("Suppliers Page", () => {
  it("renders table with suppliers", async () => {
    renderWithProviders(<SuppliersPage />);
    expect(await screen.findByText("Consorcio Metro Bogotá 2032")).toBeInTheDocument();
    expect(screen.getByText("Constructora Infraestructura Global")).toBeInTheDocument();
  });

  it("renders search input", async () => {
    renderWithProviders(<SuppliersPage />);
    expect(await screen.findByPlaceholderText("Buscar por nombre o documento...")).toBeInTheDocument();
  });

  it("renders KPI cards", async () => {
    renderWithProviders(<SuppliersPage />);
    expect(await screen.findByText("Total Proveedores")).toBeInTheDocument();
    expect(screen.getByText("Son PyME")).toBeInTheDocument();
  });

  it("renders risk badges", async () => {
    renderWithProviders(<SuppliersPage />);
    const badges = await screen.findAllByText(/Alto|Medio|Bajo/);
    expect(badges.length).toBeGreaterThanOrEqual(1);
  });
});