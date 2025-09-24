import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  /* Global timeout for each test */
  timeout: 60000, // 60 seconds (otimizado após correções de backend)

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    actionTimeout: 15000, // 15 seconds for actions (incluindo cálculos)
  },

  /* Expect timeout */
  expect: {
    timeout: 15000, // 15 seconds for assertions (aguardar resultados)
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    // Webkit disabled for now due to potential compatibility issues
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  webServer: [
    // Backend server
    {
      command: 'cd ../backend && ./.venv/bin/uvicorn src.api.main:app --reload --port 8001',
      url: 'http://localhost:8001/health',
      reuseExistingServer: !process.env.CI,
      timeout: 90000, // 90 seconds to start backend
    },
    // Frontend server
    {
      command: 'VITE_API_BASE_URL=http://localhost:8001 npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: !process.env.CI,
      timeout: 60000, // 60 seconds to start frontend
    },
  ],
});