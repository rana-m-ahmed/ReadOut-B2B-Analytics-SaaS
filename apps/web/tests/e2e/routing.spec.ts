import { test, expect } from '@playwright/test';

test.describe('Routing and Guards', () => {
  const publicRoutes = [
    '/',
    '/login',
    '/signup',
    '/connect-data',
    '/schema-preview',
    '/walkthrough',
  ];

  for (const route of publicRoutes) {
    test(`Public route ${route} resolves successfully`, async ({ page }) => {
      const response = await page.goto(route);
      expect(response?.status()).toBe(200);
    });
  }

  const protectedRoutes = [
    '/overview',
    '/ask',
    '/insights',
    '/anomalies',
    '/data-sources',
    '/settings',
  ];

  for (const route of protectedRoutes) {
    test(`Protected route ${route} redirects unauthenticated user to landing page`, async ({ page }) => {
      await page.goto(route);
      await expect(page).toHaveURL('/');
    });
  }

  test('Demo route creates anon session and allows access to dashboard', async ({ page }) => {
    await page.goto('/demo');
    await page.waitForURL('**/overview');
    expect(page.url()).toContain('/overview');
    
    const response = await page.goto('/insights');
    expect(response?.status()).toBe(200);
    expect(page.url()).toContain('/insights');
  });
});
