import { expect, test } from '@playwright/test';

for (const mobile of [false, true]) {
  test(`public notebook opens and navigates on ${mobile ? 'mobile' : 'desktop'}`, async ({ page }) => {
    await page.setViewportSize(mobile ? { width: 360, height: 780 } : { width: 1280, height: 850 });
    await page.emulateMedia({ reducedMotion: mobile ? 'reduce' : 'no-preference' });
    await page.goto('http://127.0.0.1:3000');
    await expect(page.locator('.nb')).toHaveAttribute('data-ready', 'true');
    await page.getByRole('button', { name: 'Open notebook' }).click();
    await expect(page.locator('.status')).toContainText(mobile ? 'Inside cover' : 'Contents');
    await page.keyboard.press('ArrowRight');
    await expect(page.locator('.status')).toContainText(mobile ? 'Contents' : 'Notes');
    await page.getByRole('group', { name: 'Sections' }).getByRole('button', { name: 'Dreams' }).click();
    await expect(page.locator('.status')).toContainText('Dreams');
    await page.keyboard.press('Home');
    await expect(page.getByRole('button', { name: 'Open notebook' })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  });
}
