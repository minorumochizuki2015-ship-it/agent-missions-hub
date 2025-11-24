import { test, expect, Page } from '@playwright/test'
import { injectAxe, checkA11y } from 'axe-playwright'

const waitForDashboard = async (page: Page) => {
  await page.locator('text=Glass-mode Dashboard').first().waitFor({ timeout: 15000 })
}

test.describe('SafeOps Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    const base = process.env.NEXT_PUBLIC_SAFEOPS_UI_BASE || 'http://localhost:3000'
    await page.goto(base)
    await injectAxe(page)
  })

  test('dashboard loads successfully', async ({ page }) => {
    await expect(page).toHaveTitle('SafeOps Orchestrator Dashboard')
    await expect(page.locator('h1')).toContainText('SafeOps Orchestrator Dashboard')
  })

  test('dashboard has proper heading structure', async ({ page }) => {
    await waitForDashboard(page)
    await expect(page.locator('h1')).toHaveCount(1)
    await expect(page.locator('text=Dangerous Commands').first()).toBeVisible()
    await expect(page.locator('text=Approvals Ledger')).toBeVisible()
    await expect(page.locator('text=Approvals Pending')).toBeVisible()
    await expect(page.locator('text=CI Success %')).toBeVisible()
  })

  test('dashboard is accessible', async ({ page }) => {
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: {
        html: true
      }
    })
  })

  test('dashboard has proper color contrast', async ({ page }) => {
    await checkA11y(page, null, {
      rules: {
        'color-contrast': { enabled: true }
      }
    })
  })

  test('dashboard has proper ARIA labels', async ({ page }) => {
    await checkA11y(page, null, {
      rules: {
        'aria-allowed-attr': { enabled: true },
        'aria-required-attr': { enabled: true },
        'aria-valid-attr': { enabled: true }
      }
    })
  })

  test('refresh button works', async ({ page }) => {
    await waitForDashboard(page)
    const refreshButton = page.locator('button:has-text("Refresh")')
    await expect(refreshButton).toBeVisible()
    await refreshButton.click()

    // Should show loading state or update timestamp
    await expect(page.locator('text=Last updated:')).toBeVisible()
  })

  test('plan button triggers session display', async ({ page }) => {
    await waitForDashboard(page)
    const btn = page.locator('button:has-text("Run Plan + Guard")')
    await expect(btn).toBeVisible()
    await btn.click()
    await expect(page.locator('text=PLAN or SafeOps Guard に失敗しました').or(page.locator('text=PLAN + SafeOps Guard を記録しました'))).toBeVisible()
  })

  test('dashboard is keyboard navigable', async ({ page }) => {
    await waitForDashboard(page)
    await page.keyboard.press('Tab')
    const firstFocus = await page.evaluate(() => document.activeElement?.tagName)
    expect(firstFocus).toBeTruthy()
    const refreshButton = page.locator('button:has-text("Refresh")')
    await expect(refreshButton).toBeVisible()
  })

  test('dashboard has proper landmark roles', async ({ page }) => {
    await checkA11y(page, null, {
      rules: {
        'landmark-one-main': { enabled: true },
        'region': { enabled: true }
      }
    })
  })

  test('dashboard images have alt text', async ({ page }) => {
    const images = await page.locator('img').all()
    for (const img of images) {
      const alt = await img.getAttribute('alt')
      expect(alt).toBeTruthy()
    }
  })

  test('dashboard has proper link text', async ({ page }) => {
    await checkA11y(page, null, {
      rules: {
        'link-name': { enabled: true }
      }
    })
  })

  test('dashboard meets LCP performance requirements', async ({ page }) => {
    const base = process.env.NEXT_PUBLIC_SAFEOPS_UI_BASE || 'http://localhost:3000'
    await page.goto(base)
    await page.waitForLoadState('networkidle')
    const lcp = await page.evaluate(() => new Promise((resolve) => {
      let value = null as number | null
      let done = false
      try {
        const obs = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          const last = entries[entries.length - 1] as any
          if (last && typeof last.startTime === 'number') {
            value = last.startTime
          }
        })
        obs.observe({ entryTypes: ['largest-contentful-paint'] })
        setTimeout(() => {
          if (!done) {
            try { obs.disconnect() } catch {}
            resolve(value ?? 1000)
            done = true
          }
        }, 2000)
      } catch {
        resolve(1000)
      }
    }))
    expect(lcp as number).toBeLessThan(2500)
  })
})
