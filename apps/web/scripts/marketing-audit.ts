import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  // Use incognito context
  const context = await browser.newContext();
  const page = await context.newPage();
  
  const startTime = Date.now();
  await page.goto('http://localhost:3000/');
  
  // Wait for the animation to start rendering
  await page.waitForTimeout(2000); 
  const loadTime = Date.now() - startTime;
  
  console.log(`Page visually loaded in ${loadTime}ms`);
  
  // Get all text content
  const textContent = await page.evaluate(() => document.body.innerText);
  
  const placeholders = ['lorem', 'ipsum', 'todo', 'stub', 'placeholder'];
  const found = placeholders.filter(p => textContent.toLowerCase().includes(p));
  
  if (found.length > 0) {
    console.error('Found placeholders:', found);
  } else {
    console.log('Zero unlabeled placeholders found in the visible text.');
  }
  
  await page.screenshot({ path: 'marketing_audit.png', fullPage: true });
  
  await browser.close();
})();
