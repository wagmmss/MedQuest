import { defineConfig, devices } from '@playwright/test';
import { loadEnvConfig } from '@next/env';

loadEnvConfig(process.cwd());
const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3100';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: 'list',
  timeout: 30000,
  use: {
    baseURL,
    trace: 'off',
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
      HOSTNAME: '0.0.0.0',
      FLASK_API_URL: 'http://127.0.0.1:9999',
      FLASK_API_PROXY_SECRET: 'test-proxy-secret',
      PLAYWRIGHT_TEST: 'true',
      NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || 'pk_test_mock',
      CLERK_SECRET_KEY: process.env.CLERK_SECRET_KEY || 'sk_test_mock',
    },
    // The app shell may depend on an external API, so use a static asset as
    // the readiness probe. Browser requests are mocked by the E2E suite.
    url: `${baseURL}/favicon.ico`,
    reuseExistingServer: false,
    timeout: 120000,
  },
});
