import { defineConfig, devices } from '@playwright/test';

const PORT = process.env.PORT || '4317';
const BASE_URL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [
    ['list'],
    ['json', { outputFile: 'test-results/playwright-results.json' }],
  ],
  outputDir: 'test-evidence/latest',
  use: {
    baseURL: BASE_URL,
    screenshot: 'on',
    trace: 'on-first-retry',
    video: 'retain-on-failure',
    actionTimeout: 5_000,
    navigationTimeout: 10_000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'node app/server.js',
    url: `${BASE_URL}/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 10_000,
    stdout: 'ignore',
    stderr: 'pipe',
  },
});
