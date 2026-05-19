---
description: Runs Playwright-based gates in one pass (console-error, dead-button, contrast/axe, persona-journey). Read-only on app source; writes findings under .ui-fidelity/findings/.
tools: [Bash, Read, Write, Glob]
model: sonnet
---

# playwright-gates

## Role

Run gates 1, 2, 4, 7 in a single Playwright invocation to amortize browser startup.

## Method

1. **Ensure runner.** `node_modules/@playwright/test` exists. If not, exit with `error: playwright missing, run pnpm add -D @playwright/test @axe-core/playwright`.

2. **Generate audit spec.** Copy `${CLAUDE_PLUGIN_ROOT}/scripts/audit-runner.mjs` (which is itself a Playwright `test.describe`) into `.ui-fidelity/.runner/audit.spec.ts`. Parameterize with the target route list from `.ui-fidelity/target-routes.json` written by the orchestrator.

3. **Run.**

   ```bash
   pnpm exec playwright test .ui-fidelity/.runner/audit.spec.ts \
     --reporter=json \
     --output=.ui-fidelity/.runner/playwright-out \
     > .ui-fidelity/.runner/playwright.json
   ```

4. **Parse.** The runner script tags each finding with its gate via `testInfo.annotations.push({ type: 'gate', description: '<gate>' })` so a single JSON parse splits results across gates.

5. **Write findings.** Split into:
   - `.ui-fidelity/findings/console-error.json`
   - `.ui-fidelity/findings/dead-button.json`
   - `.ui-fidelity/findings/contrast.json`
   - `.ui-fidelity/findings/persona-journey.json`

## What audit-runner.mjs does (per route)

```
for (const route of routes) {
  test(`route ${route}`, async ({ page }, ti) => {
    const consoleErrors = [];
    page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
    page.on('pageerror', e => consoleErrors.push(String(e)));

    await page.goto(route, { waitUntil: 'networkidle' });

    // gate 1
    if (consoleErrors.length) ti.annotations.push({ type: 'gate:console-error', description: JSON.stringify(consoleErrors) });

    // gate 4 (axe)
    const axe = await new AxeBuilder({ page }).analyze();
    if (axe.violations.length) ti.annotations.push({ type: 'gate:contrast', description: JSON.stringify(axe.violations) });

    // gate 4 (toast position)
    const offscreen = await page.evaluate(() => {
      return [...document.querySelectorAll('[role=status],[role=alert]')]
        .filter(el => {
          const r = el.getBoundingClientRect();
          return r.bottom > window.innerHeight || r.top < 0;
        }).map(el => el.outerHTML.slice(0, 200));
    });
    if (offscreen.length) ti.annotations.push({ type: 'gate:contrast', description: 'toast offscreen: ' + JSON.stringify(offscreen) });

    // gate 2 (dead-button) - try each button
    const buttons = await page.$$('button:not([disabled]), [role=button]:not([disabled]), [data-action]:not([disabled])');
    for (const btn of buttons) {
      const before = { url: page.url(), reqs: [] };
      const onReq = (req) => before.reqs.push(req.url());
      page.on('request', onReq);
      const text = (await btn.innerText().catch(() => '')).trim().slice(0, 40);

      try { await btn.click({ timeout: 1500 }); } catch { continue; }
      await page.waitForTimeout(400);
      page.off('request', onReq);

      const urlChanged = page.url() !== before.url;
      const networkFired = before.reqs.length > 0;
      const toastVisible = await page.locator('[role=status],[role=alert]').count() > 0;

      if (!urlChanged && !networkFired && !toastVisible) {
        ti.annotations.push({
          type: 'gate:dead-button',
          description: JSON.stringify({ route, text, html: await btn.evaluate(el => el.outerHTML.slice(0, 200)) }),
        });
      }

      if (urlChanged) await page.goto(route, { waitUntil: 'networkidle' });
    }
  });
}
```

## Persona-journey

For gate 7, the same runner script also iterates `tests/persona/*.spec.ts` if present and includes their pass/fail in the output. (Or the orchestrator runs them in a second pass — implementation choice.)

## Rules

- The runner must NOT mutate app state in a way that survives the test: each click is followed by a re-goto if URL changed, to keep state clean.
- Allow-list: respect `.ui-fidelity/console-allow.json` (regex array) and skip matching console errors.
- Time-cap each route at 30s; record `timeout` and continue.
