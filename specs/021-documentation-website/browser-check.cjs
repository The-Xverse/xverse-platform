// Optional browser acceptance checks. Install Playwright in a separate QA environment.
// PLAYWRIGHT_MODULE=/path/to/playwright node browser-check.cjs URL SCREENSHOT_DIRECTORY
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');

(async () => {
  const origin = process.argv[2];
  const screenshots = process.argv[3];
  if (!origin?.endsWith('/') || !screenshots) throw new Error('Provide a trailing-slash site URL and screenshot directory.');
  await fs.mkdir(screenshots, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const errors = [];
  const checks = [];
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, permissions: ['clipboard-read', 'clipboard-write'] });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    const visit = async route => {
      const response = await page.goto(new URL(route, origin).href, { waitUntil: 'networkidle' });
      assert.equal(response.status(), 200);
    };
    const noOverflow = async () => assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);

    await visit('');
    await page.keyboard.press('Tab');
    assert.equal(await page.locator(':focus').textContent(), 'Skip to content');
    for (const realization of ['Physical', 'Hybrid', 'Simulation']) {
      await page.getByRole('button', { name: realization, exact: true }).click();
      assert.equal(await page.getByRole('button', { name: realization, exact: true }).getAttribute('aria-pressed'), 'true');
    }
    await page.getByRole('button', { name: 'Copy XDL help command' }).click();
    assert.equal(await page.evaluate(() => navigator.clipboard.readText()), 'uv run --frozen xdl validate --help');
    await page.screenshot({ path: path.join(screenshots, 'home-desktop.png'), fullPage: true });
    checks.push('Keyboard skip link, realization controls, clipboard, desktop home');

    await page.keyboard.press('Control+k');
    const search = page.locator('#pagefind-search input');
    await search.waitFor();
    for (const [query, expected] of [['EvidenceStore', 'reference/python/'], ['StimulationGuard', 'reference/cpp/']]) {
      await search.fill(query);
      await page.waitForFunction(expected => [...document.querySelectorAll('#pagefind-search a')].some(link => link.href.includes(expected)), expected);
      const links = await page.locator('#pagefind-search a').evaluateAll(nodes => nodes.map(node => node.href));
      assert.ok(links.every(link => link.startsWith(origin)));
    }
    await page.screenshot({ path: path.join(screenshots, 'search.png') });
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#xverse-search').evaluate(dialog => dialog.open), false);
    checks.push('Keyboard search, Python and C++ results, hosting prefix, Escape close');

    await visit('docs/getting-started/first-system/');
    await page.locator('starlight-theme-select select').first().selectOption('dark');
    assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
    await page.screenshot({ path: path.join(screenshots, 'documentation-desktop.png') });
    await page.locator('starlight-theme-select select').first().selectOption('light');
    assert.equal(await page.locator('html').getAttribute('data-theme'), 'light');
    await page.setViewportSize({ width: 390, height: 844 });
    await noOverflow();
    await page.getByRole('button', { name: 'Menu', exact: true }).click();
    await page.locator('#starlight__sidebar').getByRole('link', { name: 'Overview', exact: true }).click();
    assert.ok(page.url().endsWith('/docs/'));
    await page.screenshot({ path: path.join(screenshots, 'documentation-mobile.png') });
    await visit('');
    await noOverflow();
    await page.screenshot({ path: path.join(screenshots, 'home-mobile.png'), fullPage: true });
    checks.push('Docs light/dark themes, mobile menu navigation, mobile home/docs overflow');

    for (const [kind, route] of [['python', 'reference/python/xverse-argus.html'], ['cpp', 'reference/cpp/core__types_8hpp.html']]) {
      await visit(route);
      await noOverflow();
      const back = page.getByRole('link', { name: '← X-Verse documentation' });
      assert.equal(await back.getAttribute('href'), new URL('docs/reference/', origin).pathname);
      await page.screenshot({ path: path.join(screenshots, `${kind}-mobile.png`) });
      await back.click();
      assert.ok(page.url().endsWith('/docs/reference/'));
    }
    checks.push('Native Python/C++ mobile references and return navigation');
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ browserVersion: browser.version(), site: origin, checks, errors }, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
