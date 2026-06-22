import { chromium } from 'playwright';

(async () => {
  console.log("Starting browser audit for Data Sources page...");
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Go to root page and click CTA
    console.log("Navigating to root to authenticate...");
    await page.goto('http://localhost:3000/');
    await page.waitForLoadState('networkidle');
    
    // Click CTA to sign in anonymously
    const ctaBtn = page.getByRole('button', { name: /launch demo dashboard/i });
    if (await ctaBtn.isVisible()) {
      await ctaBtn.click();
      await page.waitForURL('**/overview', { timeout: 10000 });
      console.log("Successfully authenticated and routed to overview.");
    }
    
    // Now go to data-sources
    await page.goto('http://localhost:3000/data-sources');
    await page.waitForLoadState('networkidle');

    console.log("On Data Sources page.");
    await page.waitForTimeout(2000); // Give it a moment to fetch data

    const hasDatasets = await page.locator('[data-testid="dataset-card"]').count();
    
    if (hasDatasets === 0) {
      console.log("No datasets found. Empty state displayed.");
      await page.screenshot({ path: 'data-sources-empty.png' });
    } else {
      console.log(`Found ${hasDatasets} dataset(s).`);
      
      const firstCard = page.locator('[data-testid="dataset-card"]').first();
      
      // Expand column table
      const expandBtn = firstCard.locator('button').filter({ hasText: '' }).last();
      await expandBtn.click();
      console.log("Clicked expand button.");
      await page.waitForTimeout(1000);
      
      const tableVisible = await firstCard.locator('[data-testid="column-table"]').isVisible();
      console.log(`Column table visible: ${tableVisible}`);
      
      // Attempt delete flow
      const deleteBtn = firstCard.locator('[data-testid="start-delete"]');
      await deleteBtn.click();
      console.log("Clicked start delete.");
      await page.waitForTimeout(500);

      const confirmVisible = await firstCard.locator('[data-testid="delete-confirm"]').isVisible();
      console.log(`Confirmation visible: ${confirmVisible}`);
      
      await page.screenshot({ path: 'data-sources-expanded-and-confirming.png', fullPage: true });

      const cancelBtn = firstCard.locator('[data-testid="cancel-delete"]');
      await cancelBtn.click();
      console.log("Clicked cancel delete.");
      await page.waitForTimeout(500);
      
      const confirmStillVisible = await firstCard.locator('[data-testid="delete-confirm"]').isVisible();
      console.log(`Confirmation still visible after cancel: ${confirmStillVisible}`);
    }

  } catch (err) {
    console.error("Audit failed:", err);
  } finally {
    await browser.close();
  }
})();
