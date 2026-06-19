import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button } from "@/components/ui/button";

describe("Button", () => {
  it("renders children", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: /click me/i })).toBeInTheDocument();
  });

  it("has primary variant by default", () => {
    render(<Button>Primary</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("bg-primary");
  });

  it("applies outline variant", () => {
    render(<Button variant="outline">Outline</Button>);
    const btn = screen.getByRole("button");
    expect(btn.className).toContain("border");
  });

  it("handles clicks", async () => {
    const fn = vi.fn();
    render(<Button onClick={fn}>Click</Button>);
    await userEvent.click(screen.getByRole("button"));
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("can be disabled", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("applies size variants", () => {
    render(<Button size="lg">Large</Button>);
    expect(screen.getByRole("button").className).toContain("h-12");
  });

  it("has accessible role", () => {
    render(<Button>Accessible</Button>);
    expect(screen.getByRole("button", { name: "Accessible" })).toBeInTheDocument();
  });
});