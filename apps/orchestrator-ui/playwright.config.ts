import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  outputDir: '../../artifacts/ui_audit',
  reporter: [
    ['list'],
    ['junit', { outputFile: '../../observability/test-results/junit.xml' }],
    ['html', { outputFolder: '../../artifacts/ui_audit_report', open: 'never' }],
  ],
  webServer: {
    command: 'next dev -p 3000',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 120_000,
    env: {
      NEXT_PUBLIC_SAFEOPS_API_BASE: 'http://localhost:8787',
      NEXT_PUBLIC_SAFEOPS_UI_BASE: 'http://localhost:3000',
    },
  },
})
