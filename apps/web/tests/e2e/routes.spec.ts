import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const publicRoutes = [
  "/",
  "/privacy",
  "/terms",
  "/login",
  "/signup",
  "/forgot-password",
  "/reset-password",
  "/verify-email",
];

test("full public and auth route matrix loads without horizontal overflow", async ({ page }) => {
  for (const route of publicRoutes) {
    await page.goto(route);
    await expect(page.locator("body")).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
    );
    expect(overflow, `${route} has horizontal overflow`).toBe(false);
  }
});

test("key public routes reflow at 320 CSS pixels", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 700 });
  for (const route of ["/", "/login", "/signup", "/forgot-password"]) {
    await page.goto(route);
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
    );
    expect(overflow, `${route} overflows at 320px`).toBe(false);
  }
});

test("landing skip link moves focus to primary content", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  const skipLink = page.getByRole("link", { name: "Skip to content" });
  await expect(skipLink).toBeFocused();
  await skipLink.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();
});

test("dashboard preserves next when signed out", async ({ page }) => {
  for (const route of [
    "/dashboard/overview",
    "/dashboard/ask",
    "/dashboard/insights",
    "/dashboard/anomalies",
    "/dashboard/data-sources",
    "/dashboard/settings",
  ]) {
    await page.goto(route);
    await expect(page).toHaveURL(
      new RegExp(`/login\\?next=${encodeURIComponent(route).replaceAll("%", "%")}`),
    );
  }
});

test("public and auth surfaces have no critical or serious axe violations", async ({ page }) => {
  for (const route of ["/", "/login", "/signup", "/forgot-password", "/reset-password"]) {
    await page.goto(route);
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
      .analyze();
    expect(
      result.violations.filter(
        (violation) => violation.impact === "critical" || violation.impact === "serious",
      ),
      route,
    ).toEqual([]);
  }
});

test("demo route renders without crash", async ({ page }) => {
  await page.goto("/demo");
  await expect(page.locator("body")).toBeVisible();
});
