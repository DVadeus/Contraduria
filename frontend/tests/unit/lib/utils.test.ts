import { describe, it, expect } from "vitest";
import { cn, formatCOP, formatShortCOP, formatDate, formatPercent } from "@/lib/utils";

describe("formatCOP", () => {
  it("formats COP currency correctly", () => {
    expect(formatCOP(11_250_000_000)).toContain("11.250.000.000");
    expect(formatCOP(0)).toContain("0");
    expect(formatCOP(1_500_000)).toContain("1.500.000");
  });

  it("handles null/undefined", () => {
    expect(formatCOP(null)).toBe("$ 0");
    expect(formatCOP(undefined)).toBe("$ 0");
  });

  it("uses COP locale", () => {
    const result = formatCOP(1000000);
    expect(result).toContain("$");
  });
});

describe("formatShortCOP", () => {
  it("formats billions", () => {
    expect(formatShortCOP(5_000_000_000)).toBe("$ 5.0B");
    expect(formatShortCOP(8_500_000_000)).toBe("$ 8.5B");
  });

  it("formats trillions correctly", () => {
    expect(formatShortCOP(87_300_000_000_000)).toContain("T");
  });

  it("formats millions", () => {
    expect(formatShortCOP(5_000_000)).toBe("$ 5.0M");
  });

  it("formats trillions", () => {
    expect(formatShortCOP(1_000_000_000_000)).toContain("T");
  });

  it("falls back to full format for small values", () => {
    const result = formatShortCOP(500_000);
    expect(result).toContain("$");
  });

  it("handles null/undefined", () => {
    expect(formatShortCOP(null)).toBe("$ 0");
    expect(formatShortCOP(undefined)).toBe("$ 0");
  });
});

describe("formatDate", () => {
  it("formats valid date", () => {
    expect(formatDate("2026-03-15")).toContain("2026");
  });

  it("returns dash for null/undefined/empty", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate(undefined)).toBe("—");
    expect(formatDate("")).toBe("—");
  });
});

describe("formatPercent", () => {
  it("formats percentage", () => {
    expect(formatPercent(67)).toBe("67%");
    expect(formatPercent(0)).toBe("0%");
    expect(formatPercent(100)).toBe("100%");
  });

  it("handles null/undefined", () => {
    expect(formatPercent(null)).toBe("—");
    expect(formatPercent(undefined)).toBe("—");
  });
});

describe("cn", () => {
  it("merges classes", () => {
    expect(cn("a", "b")).toBe("a b");
  });

  it("filters falsy values", () => {
    expect(cn("a", false && "b", "c")).toBe("a c");
  });

  it("handles empty input", () => {
    expect(cn()).toBe("");
  });
});