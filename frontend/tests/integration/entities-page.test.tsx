import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../utils/renderWithProviders";
import EntitiesPage from "@/app/entities";

describe("Entities Page", () => {
  it("renders table with entities", async () => {
    renderWithProviders(<EntitiesPage />);
    expect(await screen.findByText("Empresa Metro de Bogotá")).toBeInTheDocument();
    expect(screen.getByText("IDU Bogotá")).toBeInTheDocument();
    expect(screen.getByText("Secretaría de Educación")).toBeInTheDocument();
  });

  it("renders search input", async () => {
    renderWithProviders(<EntitiesPage />);
    expect(await screen.findByPlaceholderText("Buscar por nombre o NIT...")).toBeInTheDocument();
  });

  it("renders KPI cards", async () => {
    renderWithProviders(<EntitiesPage />);
    expect(await screen.findByText("Total Entidades")).toBeInTheDocument();
    expect(screen.getByText("Contratos Promedio")).toBeInTheDocument();
  });
});