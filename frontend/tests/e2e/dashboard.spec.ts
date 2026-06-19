import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test("shows KPIs", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Total Contratado")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Contratos Activos")).toBeVisible();
    await expect(page.getByText("Contratistas Únicos")).toBeVisible();
  });

  test("renders charts", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Top Entidades por Valor")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Modalidades de Contratación")).toBeVisible();
    await expect(page.getByText("Tendencia Anual")).toBeVisible();
  });

  test("has no JS errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));
    await page.goto("/");
    await page.waitForTimeout(3000);
    expect(errors).toEqual([]);
  });
});