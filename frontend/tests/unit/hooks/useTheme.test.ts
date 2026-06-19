import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useTheme } from "@/hooks/useTheme";

describe("useTheme", () => {
  beforeEach(() => {
    localStorage.removeItem("contraduria-theme");
    document.documentElement.classList.remove("dark");
  });

  it("defaults to light mode", () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.isDark).toBe(false);
  });

  it("toggles to dark mode", () => {
    const { result } = renderHook(() => useTheme());
    act(() => result.current.toggle());
    expect(result.current.isDark).toBe(true);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("toggles back to light mode", () => {
    const { result } = renderHook(() => useTheme());
    act(() => result.current.toggle());
    act(() => result.current.toggle());
    expect(result.current.isDark).toBe(false);
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("persists theme in localStorage", () => {
    const { result } = renderHook(() => useTheme());
    act(() => result.current.toggle());
    expect(localStorage.getItem("contraduria-theme")).toBe("dark");
  });

  it("reads persisted theme from localStorage", () => {
    localStorage.setItem("contraduria-theme", "dark");
    document.documentElement.classList.add("dark");
    const { result } = renderHook(() => useTheme());
    expect(result.current.isDark).toBe(true);
  });
});