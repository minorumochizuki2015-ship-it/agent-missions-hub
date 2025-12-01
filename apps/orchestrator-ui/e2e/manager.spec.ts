import { expect, test } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

const managerPath = 'http://localhost:3000/mail/manager?lang=en'

test.describe('Manager UI', () => {
  test('renders manager layout and passes axe', async ({ page }) => {
    await page.goto(managerPath)
    await expect(page.getByTestId('manager-title')).toContainText(/Manager/i)
    await expect(page.getByTestId('mission-row').first()).toBeVisible()
    await expect(page.getByTestId('taskgroup-card').first()).toBeVisible()
    await expect(page.getByTestId('artifact-card').first()).toBeVisible()

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze()
    expect(accessibilityScanResults.violations).toEqual([])

    await page.screenshot({ path: 'artifacts/ui_audit/screens/manager_en.png' })
  })
})
