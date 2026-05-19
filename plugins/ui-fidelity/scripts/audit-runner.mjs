// Playwright spec that runs gates 1, 2, 4 in one pass.
// Invoked via: pnpm exec playwright test <this-file> --reporter=json
//
// Targets come from .ui-fidelity/target-routes.json (written by the
// orchestrator). Findings emitted as testInfo.annotations so the orchestrator
// can split them per-gate after the run.
import { test, expect } from '@playwright/test';
import { AxeBuilder } from '@axe-core/playwright';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const ROUTES = JSON.parse(
  readFileSync(join(process.cwd(), '.ui-fidelity', 'target-routes.json'), 'utf-8'),
);
const ALLOW = (() => {
  try {
    return JSON.parse(
      readFileSync(join(process.cwd(), '.ui-fidelity', 'console-allow.json'), 'utf-8'),
    );
  } catch {
    return [];
  }
})();

function allowedConsoleError(msg) {
  return ALLOW.some((rule) => new RegExp(rule).test(msg));
}

for (const route of ROUTES) {
  test(`audit ${route}`, async ({ page }, ti) => {
    const consoleErrors = [];
    page.on('console', (m) => {
      if (m.type() === 'error' && !allowedConsoleError(m.text())) consoleErrors.push(m.text());
    });
    page.on('pageerror', (e) => consoleErrors.push(String(e)));

    await page.goto(route, { waitUntil: 'networkidle' }).catch(() => {});

    if (consoleErrors.length > 0) {
      ti.annotations.push({
        type: 'gate:console-error',
        description: JSON.stringify({ route, errors: consoleErrors }),
      });
    }

    // gate 4 a11y
    try {
      const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
      if (axe.violations.length > 0) {
        ti.annotations.push({
          type: 'gate:contrast',
          description: JSON.stringify({
            route,
            violations: axe.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length, help: v.help })),
          }),
        });
      }
    } catch (e) {
      ti.annotations.push({ type: 'gate:contrast', description: `axe error: ${String(e)}` });
    }

    // gate 4 toast position
    const offscreen = await page.evaluate(() => {
      return [...document.querySelectorAll('[role=status], [role=alert]')]
        .filter((el) => {
          const r = el.getBoundingClientRect();
          return r.bottom > window.innerHeight || r.top < 0 || r.right > window.innerWidth || r.left < 0;
        })
        .map((el) => ({ text: (el.textContent || '').slice(0, 80), html: el.outerHTML.slice(0, 200) }));
    });
    if (offscreen.length > 0) {
      ti.annotations.push({
        type: 'gate:contrast',
        description: JSON.stringify({ route, toastOffscreen: offscreen }),
      });
    }

    // gate 2 dead-button
    const buttonHandles = await page.$$('button:not([disabled]), [role=button]:not([disabled])');
    for (const btn of buttonHandles) {
      const text = (await btn.innerText().catch(() => '')).trim().slice(0, 40);
      if (text === '') continue;

      const beforeUrl = page.url();
      const reqs = [];
      const onReq = (req) => reqs.push(req.url());
      page.on('request', onReq);

      try {
        await btn.click({ timeout: 1500 });
      } catch {
        page.off('request', onReq);
        continue;
      }
      await page.waitForTimeout(400);
      page.off('request', onReq);

      const urlChanged = page.url() !== beforeUrl;
      const networkFired = reqs.filter((u) => !u.includes('hot-update') && !u.includes('@vite')).length > 0;
      const toastShown = (await page.locator('[role=status], [role=alert]').count()) > 0;
      const dialogShown = (await page.locator('[role=dialog], dialog').count()) > 0;

      if (!urlChanged && !networkFired && !toastShown && !dialogShown) {
        const html = await btn.evaluate((el) => el.outerHTML.slice(0, 200)).catch(() => '');
        ti.annotations.push({
          type: 'gate:dead-button',
          description: JSON.stringify({ route, text, html }),
        });
      }

      if (urlChanged) await page.goto(route, { waitUntil: 'networkidle' }).catch(() => {});
      if (dialogShown) await page.keyboard.press('Escape').catch(() => {});
    }

    // pass annotation so orchestrator knows the test ran
    ti.annotations.push({ type: 'gate:ran', description: route });
  });
}
