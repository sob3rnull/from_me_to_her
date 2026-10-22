import { defineConfig } from '@playwright/test';
import path from 'node:path';
const python = path.resolve('.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
export default defineConfig({
  testDir: './tests/e2e',
  workers: 1,
  timeout: 60000,
  use: {baseURL:'http://localhost:3001', screenshot:'only-on-failure'},
  webServer: [
    {command: `"${python}" tests/e2e/api_server.py`, url:'http://127.0.0.1:8100/api/health', timeout:60000},
    {command: 'npm run dev:vault', url:'http://localhost:3001', env:{VAULT_API_URL:'http://127.0.0.1:8100'}, timeout:60000},
    {command: 'npm run dev:public', url:'http://127.0.0.1:3000', timeout:60000},
  ],
});
