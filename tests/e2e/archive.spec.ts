import {test, expect} from '@playwright/test';
import {execFileSync} from 'node:child_process';
import path from 'node:path';

function code() {
  return execFileSync(path.resolve('.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'), ['-m','app.demo','code'], {encoding:'utf8'}).trim();
}

test('public page and owner → draft → shared → reader flow', async ({page, browser}) => {
  await page.goto('http://127.0.0.1:3000');
  await expect(page.getByRole('heading', {level:1})).toContainText('Some things');
  await page.screenshot({path:'test-results/public-desktop.png', fullPage:true});
  await page.getByRole('link', {name:/little door/}).click();
  await page.getByRole('button', {name:'Owner', exact:true}).click();
  await page.getByLabel('Username').fill('demo-owner');
  await page.getByLabel('Password', {exact:true}).fill('fictional-demo-only');
  await page.getByLabel('Authenticator code').fill(code());
  await page.getByRole('button', {name:/Continue/}).click();
  await expect(page.getByRole('heading', {name:'Leave a little something'})).toBeVisible();
  await page.getByLabel('Title', {exact:true}).fill('Private fictional draft');
  await page.getByLabel('Your words').fill('Only the owner should see this.');
  await page.getByRole('button', {name:'Save entry'}).click();
  await expect(page.getByRole('heading', {name:'Private fictional draft'})).toBeVisible();
  await page.getByLabel('Title', {exact:true}).fill('A shared fictional letter');
  await page.getByLabel('Your words').fill('<script>window.evil = true</script>');
  await page.getByLabel('Share with reader').check();
  await page.getByRole('button', {name:'Save entry'}).click();
  await expect(page.getByRole('heading', {name:'A shared fictional letter'})).toBeVisible();
  await page.screenshot({path:'test-results/owner-desktop.png', fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:'test-results/owner-mobile.png', fullPage:true});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();

  const context = await browser.newContext({viewport:{width:390,height:844}});
  const reader = await context.newPage();
  await reader.goto('http://localhost:3001');
  await reader.getByLabel('Demo: which planet has rings?').fill('saturn');
  await reader.getByLabel('Demo: tea or coffee?').fill('tea');
  await reader.getByRole('button', {name:/Continue/}).click();
  await reader.getByLabel('Anniversary').fill('2020-01-01');
  await reader.getByLabel('His full name').fill('Alex Example');
  await reader.getByRole('button', {name:/Continue/}).click();
  await reader.getByLabel('Username').fill('demo-reader');
  await reader.getByLabel('Password', {exact:true}).fill('fictional-demo-only');
  await reader.getByLabel('Authenticator code').fill(code());
  await reader.getByRole('button', {name:/Continue/}).click();
  await expect(reader.getByRole('heading', {name:'A shared fictional letter'})).toBeVisible();
  await expect(reader.getByText('Private fictional draft')).toHaveCount(0);
  await expect(reader.getByRole('button', {name:'Save entry'})).toHaveCount(0);
  await expect(reader.getByText('<script>window.evil = true</script>', {exact:true})).toBeVisible();
  expect(await reader.evaluate(() => (window as unknown as {evil?:boolean}).evil)).toBeUndefined();
  await reader.screenshot({path:'test-results/reader-mobile.png',fullPage:true});
  await reader.getByRole('button', {name:'Sign out'}).click();
  await expect(reader.getByRole('heading', {name:'Step 1 of 3'})).toBeVisible();
  await context.close();
});
