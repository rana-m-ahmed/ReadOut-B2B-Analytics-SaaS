import { test, expect } from '@playwright/test';

test.describe('In-app Navigation and Layout', () => {
  test('Desktop: Sidebar routes are reachable via click and docks are floating', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.goto('/demo');
    await page.waitForURL('**/overview');

    // Check margin and radius on sidebar to confirm it's floating
    const sidebar = page.locator('data-testid=sidebar');
    await expect(sidebar).toBeVisible();
    
    // Evaluate computed styles
    const styles = await sidebar.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return {
        marginTop: computed.marginTop,
        marginLeft: computed.marginLeft,
        borderRadius: computed.borderRadius,
      };
    });
    
    // It should have margin (not 0px), meaning it's floating
    expect(styles.marginTop).not.toBe('0px');
    expect(styles.marginLeft).not.toBe('0px');
    // It should have border radius
    expect(styles.borderRadius).not.toBe('0px');

    // Navigate through routes via sidebar clicks
    const routes = [
      { name: 'Ask', path: '/ask' },
      { name: 'Insights', path: '/insights' },
      { name: 'Anomalies', path: '/anomalies' },
      { name: 'Data Sources', path: '/data-sources' },
      { name: 'Settings', path: '/settings' },
      { name: 'Overview', path: '/overview' },
    ];

    for (const route of routes) {
      await sidebar.locator(`text=${route.name}`).click();
      await page.waitForURL(`**${route.path}`);
      expect(page.url()).toContain(route.path);
    }
  });

  test('Mobile: MobileNav routes are reachable via click and docks are floating', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/demo');
    await page.waitForURL('**/overview');

    const mobileNav = page.locator('data-testid=mobile-nav');
    await expect(mobileNav).toBeVisible();

    const sidebar = page.locator('data-testid=sidebar');
    await expect(sidebar).toBeHidden();

    // Check margin/bottom on mobile nav
    const styles = await mobileNav.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return {
        bottom: computed.bottom,
        left: computed.left,
        right: computed.right,
        borderRadius: computed.borderRadius
      };
    });
    
    expect(styles.bottom).not.toBe('0px'); // Detached from bottom
    expect(styles.borderRadius).not.toBe('0px');

    // Click mobile routes
    const mobileRoutes = [
      { name: 'Ask', path: '/ask' },
      { name: 'Insights', path: '/insights' },
      { name: 'Settings', path: '/settings' },
      { name: 'Overview', path: '/overview' },
    ];

    for (const route of mobileRoutes) {
      await mobileNav.locator(`text=${route.name}`).click();
      await page.waitForURL(`**${route.path}`);
      expect(page.url()).toContain(route.path);
    }
  });
});
