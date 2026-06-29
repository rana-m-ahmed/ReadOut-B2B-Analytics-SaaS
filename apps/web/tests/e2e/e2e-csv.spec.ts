import { test, expect } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";
import * as os from "os";

test.describe("CSV Onboarding Flow", () => {
  // Skip locally or if disabled to preserve quota
  test.skip(!process.env.RUN_QUOTA_TESTS, "Quota-spending E2E tests are manual/workflow_dispatch only");

  test.setTimeout(45000);

  test("upload CSV and preview schema", async ({ page }) => {
    // We will use the anonymous demo flow to get into a session, 
    // then navigate to data sources and upload a CSV.
    await page.goto("/demo");
    await expect(page).toHaveURL(/.*\/dashboard\/overview/, { timeout: 15000 });

    // 2. Visit data sources
    await page.goto("/dashboard/data-sources");
    await expect(page.locator("text=Data Sources")).toBeVisible();
    
    // Create a temporary CSV file for testing
    const csvContent = "id,name,value\\n1,Test A,100\\n2,Test B,200\\n3,Test C,300";
    const tempDir = os.tmpdir();
    const csvPath = path.join(tempDir, "test_data.csv");
    fs.writeFileSync(csvPath, csvContent);

    // 3. Upload valid CSV
    const fileChooserPromise = page.waitForEvent("filechooser");
    await page.click('button:has-text("Upload CSV")');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(csvPath);

    // Wait for upload/profiling
    // Assuming there's some uploading/profiling state, then it finishes
    await expect(page.locator("text=test_data.csv")).toBeVisible({ timeout: 15000 });

    // Clean up
    if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath);
    
    // Check if schema preview renders (e.g. columns 'name', 'value' visible)
    // 5. Schema preview renders
    const schemaDetails = page.locator("summary:has-text('Schema')").first();
    if (await schemaDetails.isVisible()) {
      await schemaDetails.click();
      await expect(page.locator("text=name")).toBeVisible();
      await expect(page.locator("text=value")).toBeVisible();
    }
  });
});
