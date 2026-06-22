import { test, expect } from '@playwright/test';

test.describe('Demo Script End-to-End', () => {
  test('Executes 4-turn demo script and maintains context', async ({ page }) => {
    test.setTimeout(120000);
    
    // 1. Go to demo session (will auto-login if needed)
    await page.goto('/demo');
    // Wait for the redirect to settle
    await page.waitForURL('**/connect-data');

    // 2. Connect Demo Dataset
    await page.goto('/data-sources');
    await page.getByRole('button', { name: 'Use Demo Dataset' }).click();
    
    // Wait for the redirect to /overview which sets the active dataset
    await page.waitForURL('**/overview');

    // 3. Navigate to Ask
    await page.goto('/ask');
    
    // Also wait for the input to become enabled (dataset selected)
    const inputLocator = page.locator('input[type="text"], textarea');
    await expect(inputLocator).toBeEnabled({ timeout: 15000 });

    // Helper to ask a question
    async function askQuestion(q: string) {
      await page.fill('input[type="text"], textarea', q);
      await page.keyboard.press('Enter');
    }

    // Turn 1: Fresh Question
    await askQuestion('What is the total revenue for the last 30 days?');
    // Wait for the result - typically a large number
    await expect(page.locator('text=Total Revenue').or(page.locator('.text-4xl'))).toBeVisible({ timeout: 15000 });

    // Turn 2: Context reference "that"
    await askQuestion('break that down by region');
    // Wait for the chart to render. If context resolves properly, it should still be "revenue" but broken by "region"
    // Expect a chart element to appear
    await expect(page.locator('.recharts-wrapper, svg.recharts-surface').first()).toBeVisible({ timeout: 15000 });

    // Turn 3: Compare with previous
    await askQuestion('compare with previous period');
    await expect(page.locator('.recharts-wrapper, svg.recharts-surface').first()).toBeVisible({ timeout: 15000 });

    // Turn 4: Show as a bar chart
    await askQuestion('show as a bar chart');
    await expect(page.locator('.recharts-cartesian-axis').first()).toBeVisible({ timeout: 15000 });
  });
});
