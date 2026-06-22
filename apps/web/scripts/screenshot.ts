import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  
  // Desktop
  const contextDesktop = await browser.newContext({ viewport: { width: 1200, height: 800 } });
  const pageDesktop = await contextDesktop.newPage();
  await pageDesktop.goto('http://localhost:3000/demo');
  await pageDesktop.waitForURL('**/overview');
  // Wait for the shell to render
  await pageDesktop.waitForTimeout(1000);
  await pageDesktop.screenshot({ path: 'desktop.png' });
  
  // Mobile
  const contextMobile = await browser.newContext({ viewport: { width: 375, height: 812 } });
  const pageMobile = await contextMobile.newPage();
  await pageMobile.goto('http://localhost:3000/demo');
  await pageMobile.waitForURL('**/overview');
  await pageMobile.waitForTimeout(1000);
  await pageMobile.screenshot({ path: 'mobile.png' });

  await browser.close();
  console.log('Screenshots taken.');
})();
