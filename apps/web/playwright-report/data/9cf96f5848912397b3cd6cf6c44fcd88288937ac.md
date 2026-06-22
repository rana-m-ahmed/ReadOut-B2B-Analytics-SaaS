# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: demo-script.spec.ts >> Demo Script End-to-End >> Executes 4-turn demo script and maintains context
- Location: tests\e2e\demo-script.spec.ts:4:7

# Error details

```
Test timeout of 120000ms exceeded.
```

```
Error: page.waitForURL: Test timeout of 120000ms exceeded.
=========================== logs ===========================
waiting for navigation to "**/overview" until "load"
  navigated to "http://localhost:3000/demo"
  navigated to "http://localhost:3000/connect-data"
============================================================
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e6] [cursor=pointer]:
    - button "Open Next.js Dev Tools" [ref=e7]:
      - img [ref=e8]
    - generic [ref=e11]:
      - button "Open issues overlay" [ref=e12]:
        - generic [ref=e13]:
          - generic [ref=e14]: "1"
          - generic [ref=e15]: "2"
        - generic [ref=e16]:
          - text: Issue
          - generic [ref=e17]: s
      - button "Collapse issues badge" [ref=e18]:
        - img [ref=e19]
  - alert [ref=e21]
  - generic [ref=e22]:
    - generic [ref=e23]:
      - heading "Connect your data" [level=1] [ref=e24]
      - paragraph [ref=e25]: Upload a CSV file to get started. We'll automatically profile it and map the schema.
    - generic [ref=e27] [cursor=pointer]:
      - img [ref=e28]
      - heading "Drag & Drop your CSV here" [level=3] [ref=e31]
      - paragraph [ref=e32]: or click to browse from your computer
      - paragraph [ref=e33]: "Max file size: 50MB"
  - generic:
    - generic:
      - generic: Demo session — resets in 72 hours
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Demo Script End-to-End', () => {
  4  |   test('Executes 4-turn demo script and maintains context', async ({ page }) => {
  5  |     test.setTimeout(120000);
  6  |     
  7  |     // 1. Go to demo session (will auto-login if needed)
  8  |     await page.goto('/demo');
  9  |     // Wait for the redirect to settle
  10 |     await page.waitForURL('**/connect-data');
  11 | 
  12 |     // 2. Connect Demo Dataset
  13 |     await page.goto('/data-sources');
  14 |     await page.getByRole('button', { name: 'Use Demo Dataset' }).click();
  15 |     
  16 |     // Wait for the redirect to /overview which sets the active dataset
> 17 |     await page.waitForURL('**/overview');
     |                ^ Error: page.waitForURL: Test timeout of 120000ms exceeded.
  18 | 
  19 |     // 3. Navigate to Ask
  20 |     await page.goto('/ask');
  21 |     
  22 |     // Also wait for the input to become enabled (dataset selected)
  23 |     const inputLocator = page.locator('input[type="text"], textarea');
  24 |     await expect(inputLocator).toBeEnabled({ timeout: 15000 });
  25 | 
  26 |     // Helper to ask a question
  27 |     async function askQuestion(q: string) {
  28 |       await page.fill('input[type="text"], textarea', q);
  29 |       await page.keyboard.press('Enter');
  30 |     }
  31 | 
  32 |     // Turn 1: Fresh Question
  33 |     await askQuestion('What is the total revenue for the last 30 days?');
  34 |     // Wait for the result - typically a large number
  35 |     await expect(page.locator('text=Total Revenue').or(page.locator('.text-4xl'))).toBeVisible({ timeout: 15000 });
  36 | 
  37 |     // Turn 2: Context reference "that"
  38 |     await askQuestion('break that down by region');
  39 |     // Wait for the chart to render. If context resolves properly, it should still be "revenue" but broken by "region"
  40 |     // Expect a chart element to appear
  41 |     await expect(page.locator('.recharts-wrapper, svg.recharts-surface').first()).toBeVisible({ timeout: 15000 });
  42 | 
  43 |     // Turn 3: Compare with previous
  44 |     await askQuestion('compare with previous period');
  45 |     await expect(page.locator('.recharts-wrapper, svg.recharts-surface').first()).toBeVisible({ timeout: 15000 });
  46 | 
  47 |     // Turn 4: Show as a bar chart
  48 |     await askQuestion('show as a bar chart');
  49 |     await expect(page.locator('.recharts-cartesian-axis').first()).toBeVisible({ timeout: 15000 });
  50 |   });
  51 | });
  52 | 
```