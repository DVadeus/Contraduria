import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge } from "@/components/ui/badge";

describe("Badge", () => {
  it("renders children", () => {
    render(<Badge>Activo</Badge>);
    expect(screen.getByText("Activo")).toBeInTheDocument();
  });

  it("has default variant", () => {
    render(<Badge>Default</Badge>);
    expect(screen.getByText("Default").className).toContain("border");
  });

  it("applies primary variant", () => {
    render(<Badge variant="primary">Primary</Badge>);
    expect(screen.getByText("Primary").className).toContain("bg-primary");
  });

  it("applies success variant", () => {
    render(<Badge variant="success">Success</Badge>);
    expect(screen.getByText("Success").className).toContain("text-success");
  });

  it("applies warning variant", () => {
    render(<Badge variant="warning">Warning</Badge>);
    expect(screen.getByText("Warning").className).toContain("text-warning");
  });

  it("applies danger variant", () => {
    render(<Badge variant="danger">Danger</Badge>);
    expect(screen.getByText("Danger").className).toContain("text-danger");
  });
});