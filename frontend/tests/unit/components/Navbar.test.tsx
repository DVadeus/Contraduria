import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Navbar } from "@/components/layout/navbar";
import { renderWithProviders } from "../../utils/renderWithProviders";

function renderNavbar(isDark = false) {
  const toggle = vi.fn();
  const { container } = renderWithProviders(
    <Navbar isDark={isDark} onToggleTheme={toggle} />,
    { initialRoute: "/" },
  );
  return { toggle, container };
}

describe("Navbar", () => {
  it("renders logo", () => {
    renderNavbar();
    expect(screen.getByText("Contraduría")).toBeInTheDocument();
  });

  it("renders navigation links", () => {
    renderNavbar();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Contratos")).toBeInTheDocument();
    expect(screen.getByText("Entidades")).toBeInTheDocument();
    expect(screen.getByText("Proveedores")).toBeInTheDocument();
  });

  it("renders search input", () => {
    renderNavbar();
    expect(screen.getByPlaceholderText("Buscar contratos...")).toBeInTheDocument();
  });

  it("renders theme toggle button", () => {
    renderNavbar();
    expect(screen.getByLabelText(/modo/i)).toBeInTheDocument();
  });

  it("calls theme toggle on click", async () => {
    const { toggle } = renderNavbar();
    await userEvent.click(screen.getByLabelText(/modo/i));
    expect(toggle).toHaveBeenCalledTimes(1);
  });

  it("has accessible navigation role", () => {
    renderNavbar();
    const nav = screen.getByRole("navigation");
    expect(nav).toBeInTheDocument();
  });

  it("displays moon icon in light mode", () => {
    renderNavbar(false);
    expect(screen.getByLabelText("Modo oscuro")).toBeInTheDocument();
  });

  it("displays sun icon in dark mode", () => {
    renderNavbar(true);
    expect(screen.getByLabelText("Modo claro")).toBeInTheDocument();
  });
});