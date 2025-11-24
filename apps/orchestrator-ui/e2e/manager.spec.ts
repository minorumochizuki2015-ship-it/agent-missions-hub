import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Manager UI Audit', () => {
    test('Missions List Page', async ({ page }) => {
        await page.goto('http://localhost:3000/missions');

        // Wait for content
        await expect(page.locator('h1')).toContainText('Missions');

        // Axe Audit
        const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
        expect(accessibilityScanResults.violations).toEqual([]);

        // Screenshot
        await page.screenshot({ path: 'artifacts/ui_audit/screens/missions_list.png' });
    });

    // Note: We need a seeded mission to test the detail page. 
    // For now, we'll skip the detail page test until we have a reliable way to seed data in the test environment.
    // Or we could mock the API response.
});
