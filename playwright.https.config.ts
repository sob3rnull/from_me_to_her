import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/https',
  workers: 1,
  timeout: 60000,
  use: {
    baseURL: 'https://vault.localhost:8443',
    ignoreHTTPSErrors: true, // Disposable CA; never installed into the machine trust store.
    launchOptions: {args: ['--host-resolver-rules=MAP *.localhost 127.0.0.1']},
    screenshot: 'only-on-failure',
  },
});
