import {test, expect} from '@playwright/test';
import {execFileSync} from 'node:child_process';
import path from 'node:path';

const vault = 'https://vault.localhost:8443';
function code() {
  return execFileSync(path.resolve('.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'),
    ['-m', 'app.demo', 'code'], {encoding: 'utf8'}).trim();
}

test('production CSP uses fresh nonces and blocks injected scripts', async ({page}) => {
  const violations: string[] = [];
  page.on('console', message => {
    if (/Content Security Policy|violates.*directive/i.test(message.text())) violations.push(message.text());
  });
  const response = await page.goto('/');
  await expect(page.getByRole('heading', {name: 'Step 1 of 3'})).toBeVisible();
  expect(violations).toEqual([]); // Framework scripts/styles must work under enforcement.
  const csp = response!.headers()['content-security-policy'];
  expect(csp).not.toMatch(/unsafe-inline|unsafe-eval/);
  expect(csp).toContain("frame-ancestors 'none'");
  const nonce = csp.match(/'nonce-([^']+)'/)![1];
  expect(await page.locator('script').evaluateAll(elements => elements.every(element => (element as HTMLScriptElement).nonce.length > 0))).toBeTruthy();
  // Inject into the received HTML, so the browser parser enforces CSP normally.
  // DevTools evaluation is privileged and is not a valid CSP attack simulation.
  await page.route(`${vault}/`, async route => {
    const original = await route.fetch();
    const html = (await original.text()).replace('</head>', '<script>window.injected=true</script></head>');
    await route.fulfill({response: original, body: html});
  }, {times: 1});
  const next = await page.reload();
  await expect(page.getByRole('heading', {name: 'Step 1 of 3'})).toBeVisible();
  expect(await page.evaluate(() => (window as unknown as {injected?: boolean}).injected)).toBeUndefined();
  await expect.poll(() => violations.length).toBeGreaterThan(0);
  expect(next!.headers()['content-security-policy']).not.toContain(`'nonce-${nonce}'`);
  expect(next!.headers()['cache-control']).toContain('no-store');
});

test('HTTPS owner → share → reader → unshare, CSRF and recovery', async ({page, browser}) => {
  await page.goto('https://public.localhost:8444');
  await expect(page.getByRole('heading', {level: 1})).toContainText('Some things');
  await page.goto(vault);
  await page.getByRole('button', {name: 'Owner', exact: true}).click();
  await page.getByLabel('Username').fill('test-owner');
  await page.getByLabel('Password', {exact: true}).fill('fictional-demo-only');
  await page.getByLabel('Authenticator code').fill(code());
  await page.getByRole('button', {name: /Continue/}).click();
  await expect(page.getByRole('heading', {name: 'Leave a little something'})).toBeVisible();
  const cookie = (await page.context().cookies()).find(item => item.name === '__Host-vault_session')!;
  expect(cookie).toMatchObject({secure: true, httpOnly: true, sameSite: 'Strict', path: '/', domain: 'vault.localhost'});
  const bootstrap = await page.request.get(`${vault}/api/auth/session`);
  const {csrf} = await bootstrap.json();
  expect(bootstrap.headers()['cache-control']).toContain('no-store');
  expect(bootstrap.headers()['strict-transport-security']).toContain('max-age=31536000');
  const entry = {category: 'Letters', title: 'HTTPS fictional letter', body: '<script>window.evil=true</script>', shared: true};
  for (const headers of [
    {origin: 'https://evil.test', 'x-csrf-token': csrf},
    {origin: vault, 'x-csrf-token': 'wrong'},
  ]) {
    expect((await page.request.post(`${vault}/api/entries`, {data: entry, headers})).status()).toBe(403);
  }
  await page.getByLabel('Title', {exact: true}).fill(entry.title);
  await page.getByLabel('Your words').fill(entry.body);
  await page.getByLabel('Share with reader').check();
  await page.getByRole('button', {name: 'Save entry'}).click();
  await expect(page.getByRole('heading', {name: entry.title})).toBeVisible();
  const saved = (await (await page.request.get(`${vault}/api/entries`)).json())[0];

  const context = await browser.newContext({ignoreHTTPSErrors: true, viewport: {width: 390, height: 844}});
  try {
    const reader = await context.newPage();
    expect((await context.request.get(`${vault}/api/entries/${saved.id}`)).status()).toBe(401);
    await reader.goto(vault);
    await reader.getByLabel('Demo: which planet has rings?').fill('saturn');
    await reader.getByLabel('Demo: tea or coffee?').fill('tea');
    await reader.getByRole('button', {name: /Continue/}).click();
    await reader.getByLabel('Anniversary').fill('2020-01-01');
    await reader.getByLabel('His full name').fill('Alex Example');
    await reader.getByRole('button', {name: /Continue/}).click();
    await reader.getByLabel('Username').fill('test-reader');
    await reader.getByLabel('Password', {exact: true}).fill('fictional-demo-only');
    await reader.getByLabel('Authenticator code').fill(code());
    await reader.getByRole('button', {name: /Continue/}).click();
    await expect(reader.getByRole('heading', {name: entry.title})).toBeVisible();
    await expect(reader.getByText(entry.body, {exact: true})).toBeVisible();
    expect(await reader.evaluate(() => (window as unknown as {evil?: boolean}).evil)).toBeUndefined();
    const unshare = await page.request.put(`${vault}/api/entries/${saved.id}`, {
      data: {...entry, shared: false}, headers: {origin: vault, 'x-csrf-token': csrf},
    });
    expect(unshare.status()).toBe(200);
    expect((await context.request.get(`${vault}/api/entries/${saved.id}`)).status()).toBe(404);
    await reader.reload();
    await expect(reader.getByRole('heading', {name: entry.title})).toHaveCount(0);
    await page.screenshot({path: 'test-results/https-owner.png', fullPage: true});

    await page.getByRole('button', {name: 'Sign out'}).click();
    await page.getByRole('button', {name: 'Use a recovery code'}).click();
    await page.getByLabel('Username').fill('test-owner');
    await page.getByLabel('Password', {exact: true}).fill('fictional-demo-only');
    await page.getByLabel('Recovery code', {exact: true}).fill('a'.repeat(32));
    await page.getByRole('button', {name: /Continue/}).click();
    await expect(page.getByRole('status')).toContainText('Recovery code accepted');
    await page.getByRole('button', {name: 'Sign out'}).click();
    await page.getByLabel('Username').fill('test-owner');
    await page.getByLabel('Password', {exact: true}).fill('fictional-demo-only');
    await page.getByLabel('Recovery code', {exact: true}).fill('a'.repeat(32));
    await page.getByRole('button', {name: /Continue/}).click();
    await expect(page.getByRole('alert').filter({hasText: 'Unable to sign in'})).toBeVisible();
  } finally {
    await context.close();
  }
});
