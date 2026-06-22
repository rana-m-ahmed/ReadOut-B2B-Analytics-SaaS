import { chromium } from 'playwright';

(async () => {
  console.log("Starting browser verification for Dashboard KPIs...");
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to root to trigger auth
    console.log("Navigating to root to authenticate...");
    await page.goto('http://localhost:3000/');
    await page.waitForLoadState('networkidle');
    
    const ctaBtn = page.getByRole('button', { name: /launch demo dashboard/i });
    if (await ctaBtn.isVisible()) {
      await ctaBtn.click();
      console.log("Clicked CTA, waiting for redirect to overview...");
      await page.waitForURL('**/overview', { timeout: 15000 });
      console.log("Successfully authenticated and routed to overview.");
    } else {
      console.log("Already authenticated or CTA not found, navigating directly to overview.");
      await page.goto('http://localhost:3000/overview');
      await page.waitForLoadState('networkidle');
    }

    console.log("On Overview page, waiting for KPIs to load...");
    
    // Wait for the populated state to appear (it replaces the loading state)
    await page.waitForSelector('[data-testid="dashboard-populated"]', { timeout: 30000 });
    console.log("Dashboard populated state loaded.");
    
    // Additional wait for charts/data to settle
    await page.waitForTimeout(5000);

    const kpiCards = page.locator('[data-testid="metric-card"]');
    const count = await kpiCards.count();
    
    console.log(`Found ${count} KPI Metric Cards.`);
    
    for (let i = 0; i < count; i++) {
      const card = kpiCards.nth(i);
      const label = await card.locator('[data-testid="metric-label"]').innerText().catch(() => 'Unknown');
      const value = await card.locator('[data-testid="metric-value"]').innerText().catch(() => 'Unknown');
      console.log(`KPI [${i + 1}]: ${label} = ${value}`);
    }

    await page.screenshot({ path: 'dashboard-overview-kpis.png', fullPage: true });
    console.log("Screenshot saved to dashboard-overview-kpis.png");

  } catch (err) {
    console.error("Audit failed:", err);
    await page.screenshot({ path: 'dashboard-overview-error.png', fullPage: true }).catch(() => {});
  } finally {
    await browser.close();
  }
})();
