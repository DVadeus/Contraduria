import { test, expect } from "@playwright/test";

test.describe("Contracts", () => {
  test("opens contracts page and sees table", async ({ page }) => {
    await page.goto("/contratos");
    await expect(page.getByText("Contratos")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("LP-EMB-002-2026")).toBeVisible();
  });

  test("applies year filter", async ({ page }) => {
    await page.goto("/contratos");
    await page.selectOption("select", { index: 1 });
    await expect(page.locator("table")).toBeVisible();
  });
});