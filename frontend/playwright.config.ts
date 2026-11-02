import { defineConfig } from '@playwright/test'
import os from 'node:os'
import path from 'node:path'

const secretoE2E = 'Secreto-E2E-local-aleatorio-y-no-real-2026-32-bytes'
const temporalE2E = process.env.ODONTOLOGIA_E2E_TEMP_ROOT
  ?? process.env.TEMP
  ?? process.env.TMP
  ?? path.join(os.tmpdir(), 'tp-odontologia-e2e')
process.env.ODONTOLOGIA_E2E_TEMP_ROOT = temporalE2E

export default defineConfig({
  testDir: './e2e',
  testMatch: '*.spec.ts',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: 'list',
  globalTeardown: './e2e/teardown.ts',
  use: {
    baseURL: 'http://127.0.0.1:5173',
    browserName: 'chromium',
    trace: 'retain-on-failure',
    viewport: { width: 1280, height: 900 },
  },
  webServer: [
    {
      command: '..\\.venv\\Scripts\\python.exe e2e\\servidor_demo.py',
      url: 'http://127.0.0.1:8180/health',
      reuseExistingServer: false,
      timeout: 60_000,
      env: {
        JWT_SECRETO: secretoE2E,
        ODONTOLOGIA_E2E_TEMP_ROOT: temporalE2E,
      },
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      command: 'npm run dev -- --host 127.0.0.1',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: false,
      timeout: 60_000,
      env: { VITE_PROXY_TARGET: 'http://127.0.0.1:8180' },
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
})
