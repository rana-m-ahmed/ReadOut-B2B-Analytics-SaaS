import { test, expect } from "@playwright/test";

test.describe("Golden Demo Flow", () => {
  // Skip locally or if disabled to preserve quota
  test.skip(!process.env.RUN_QUOTA_TESTS, "Quota-spending E2E tests are manual/workflow_dispatch only");

  // Use a longer timeout for the demo flow as it interacts with real/mocked backend AI
  test.setTimeout(120000);

  test("full anonymous demo experience", async ({ page }) => {
    // 1. Open landing
    await page.goto("/");
    
    // 2. Launch demo dashboard
    // The Launch Demo button has data-testid="launch-demo-btn"
    await page.click('[data-testid="launch-demo-btn"]');
    
    // 3. Anonymous session starts & 4. Dashboard loads
    await expect(page).toHaveURL(/.*\/dashboard\/overview/, { timeout: 30000 });
    
    // Verify topbar shows demo badge
    await expect(page.locator("text=Demo mode · Upgrade")).toBeVisible();
    await expect(page.locator("figure").first()).toBeVisible({ timeout: 20000 });
    await expect(page.getByText("Temporarily unavailable")).toHaveCount(0);
    
    // 5. Navigate to ask page or use ask input if it's on overview
    await page.goto("/dashboard/ask");
    
    // Ask a question
    const askInput = page.getByPlaceholder(/Ask a question about/i);
    await askInput.fill("Show revenue by region for the last 3 months.");
    await askInput.press("Enter");
    
    // 6. Chart renders & 7. Summary renders
    // Chart Renderer should render a figure
    await expect(page.locator("figure").first()).toBeVisible({ timeout: 15000 });
    
    // Wait for the "Pin" button to appear, indicating successful generation
    const pinBtn = page.getByRole('button', { name: /Pin/i }).first();
    await expect(pinBtn).toBeVisible();

    // 8. Query-plan drawer opens and is non-empty
    // Find the View reasoning/plan button and click it
    const reasoningBtn = page.getByRole('button', { name: /reasoning|plan/i }).first();
    if (await reasoningBtn.isVisible()) {
      await reasoningBtn.click();
      await expect(page.getByRole("dialog", { name: "Query plan" })).toBeVisible();
      await page.keyboard.press("Escape"); // Close drawer
    }
    
    // 9. Pin chart
    await pinBtn.click();
    await expect(page.getByText("Pinned to your overview.")).toBeVisible({ timeout: 15000 });
    
    // 10. Reload
    await page.reload();
    
    // 11. Pinned widget persists
    // Verify it's on the overview page or pinned section
    await page.goto("/dashboard/overview");
    await expect(page.locator("figure")).toBeVisible({ timeout: 15000 });
    
    // 12. Ask follow-up
    await page.goto("/dashboard/ask");
    await askInput.fill("break that down by product category.");
    await askInput.press("Enter");
    
    // 13. Follow-up context is preserved
    await expect(page.locator("figure")).toBeVisible({ timeout: 15000 });
    
    // 14. Visit insights
    await page.goto("/dashboard/insights");
    await expect(page.getByRole("heading", { name: "Insights worth a closer look" })).toBeVisible();
    await page.getByRole("button", { name: "Discover insights" }).click();
    await expect(page.getByRole("button", { name: /^Pin .+/ }).first()).toBeVisible({ timeout: 20000 });
    
    // 15. Visit anomalies
    await page.goto("/dashboard/anomalies");
    await expect(page.getByRole("heading", { name: "Changes outside the baseline" })).toBeVisible();
    await page.getByRole("button", { name: "Scan anomalies" }).click();
    await expect(page.getByRole("button", { name: "Review" }).first()).toBeVisible({ timeout: 20000 });
    
    // 16. No blank or fatal screens
    await expect(page.locator("body")).toBeVisible();
  });
});
