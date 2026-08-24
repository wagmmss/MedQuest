import { defineConfig, devices } from '@playwright/test';
import { loadEnvConfig } from '@next/env';

loadEnvConfig(process.cwd());
const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:3100';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 4,
  reporter: 'html',
  timeout: 60000,
  use: {
    baseURL,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'node .next/standalone/server.js',
    env: {
      PORT: '3100',
      HOSTNAME: '127.0.0.1',
    },
    // The app shell may depend on an external API, so use a static asset as
    // the readiness probe. Browser requests are mocked by the E2E suite.
    url: `${baseURL}/favicon.ico`,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
