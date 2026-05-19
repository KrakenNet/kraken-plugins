#!/usr/bin/env node
// Static intent-contract gate.
// For each route file referenced by the target list (or all routes if --all),
// check (a) sibling INTENT.md exists, (b) primary-cta target matches actual
// handler destination, (c) no prohibited components are imported.
import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, dirname, basename, relative } from 'node:path';

const PROJECT = process.cwd();
const OUT = join(PROJECT, '.ui-fidelity', 'findings', 'intent-contract.json');

const args = process.argv.slice(2);
const all = args.includes('--all');

function walk(dir, out = []) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) {
      if (entry === 'node_modules' || entry === '.ui-fidelity' || entry.startsWith('.')) continue;
      walk(full, out);
    } else if (/\.(tsx|jsx)$/.test(entry)) {
      out.push(full);
    }
  }
  return out;
}

function parseIntent(text) {
  // crude YAML-frontmatter parse: extract route, persona, primary-cta block, prohibited list
  const out = { 'primary-cta': {}, prohibited: [], 'secondary-ctas': [] };
  const lines = text.split(/\r?\n/);
  let mode = null;
  for (const line of lines) {
    const top = line.match(/^(\w[\w-]*):\s*(.*)$/);
    if (top) {
      mode = top[1];
      const val = top[2].trim();
      if (val !== '' && val !== '[]') out[top[1]] = val;
      else if (val === '[]') out[top[1]] = [];
      continue;
    }
    const sub = line.match(/^\s{2,}([\w-]+):\s*(.+)$/);
    if (sub && mode === 'primary-cta') {
      out['primary-cta'][sub[1]] = sub[2].trim();
      continue;
    }
    const item = line.match(/^\s*-\s+(.+)$/);
    if (item) {
      if (mode === 'prohibited') out.prohibited.push(item[1].trim().replace(/^['"`]|['"`]$/g, '').split('#')[0].trim());
      if (mode === 'secondary-ctas') out['secondary-ctas'].push(item[1].trim());
    }
  }
  return out;
}

function findIntentForRoute(routeFile) {
  const dir = dirname(routeFile);
  const named = join(dir, `${basename(routeFile, '.tsx')}.INTENT.md`);
  if (existsSync(named)) return named;
  const generic = join(dir, 'INTENT.md');
  if (existsSync(generic)) return generic;
  return null;
}

function findRouteFiles() {
  const routesDir = join(PROJECT, 'src', 'routes');
  if (existsSync(routesDir)) return walk(routesDir);
  return walk(join(PROJECT, 'src'));
}

const routeFiles = findRouteFiles();
const findings = [];

for (const file of routeFiles) {
  const intentPath = findIntentForRoute(file);
  const rel = relative(PROJECT, file);

  if (intentPath == null) {
    if (all) {
      findings.push({
        gate: 'intent-contract',
        severity: 'warn',
        file: rel,
        kind: 'missing-intent',
        why: 'no INTENT.md sibling for this route file',
        'fix-hint': `run /ui-fidelity:intent ${rel}`,
      });
    }
    continue;
  }

  const intent = parseIntent(readFileSync(intentPath, 'utf-8'));
  const src = readFileSync(file, 'utf-8');

  // CTA wiring check
  const ctaLabel = intent['primary-cta']?.label;
  const ctaTarget = intent['primary-cta']?.target;
  if (ctaLabel && ctaTarget) {
    const labelRe = new RegExp(`>\\s*${ctaLabel.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`);
    const hasLabel = labelRe.test(src);
    if (!hasLabel) {
      findings.push({
        gate: 'intent-contract',
        severity: 'error',
        file: rel,
        intent: relative(PROJECT, intentPath),
        kind: 'missing-primary-cta-label',
        why: `INTENT declares primary CTA label "${ctaLabel}" but no element with that text found in route`,
        'fix-hint': 'add an element with this label or update INTENT.md',
      });
    }

    const navMatch = ctaTarget.match(/navigate\(([^)]+)\)/);
    if (navMatch && hasLabel) {
      const path = navMatch[1].replace(/['"`]/g, '').split(/\s+/)[0];
      const prefix = path.split('/').slice(0, 3).join('/').replace(/:[^/]+/, '');
      if (!new RegExp(`navigate\\(\\s*["'\`]${prefix.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`).test(src)
          && !new RegExp(`navigate\\(\\s*\`${prefix.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`).test(src)) {
        findings.push({
          gate: 'intent-contract',
          severity: 'error',
          file: rel,
          intent: relative(PROJECT, intentPath),
          kind: 'label-behavior-mismatch',
          why: `INTENT primary-cta.target says navigate(${path}) but no navigate call to that path in source`,
          'fix-hint': 'wire the CTA handler to call navigate(...) with the declared path',
        });
      }
    }
  }

  // Prohibited components
  for (const p of intent.prohibited) {
    const tag = p.trim();
    if (tag === '') continue;
    const importRe = new RegExp(`import\\s+\\{[^}]*\\b${tag}\\b[^}]*\\}`);
    const useRe = new RegExp(`<${tag}\\b`);
    if (importRe.test(src) || useRe.test(src)) {
      findings.push({
        gate: 'intent-contract',
        severity: 'error',
        file: rel,
        intent: relative(PROJECT, intentPath),
        kind: 'prohibited-component',
        component: tag,
        why: `INTENT prohibits ${tag} on this surface but it is imported or rendered`,
        'fix-hint': 'remove the component or update INTENT.prohibited if the prohibition is no longer valid',
      });
    }
  }
}

writeFileSync(OUT, JSON.stringify({ pass: findings.length === 0, findings }, null, 2));
console.log(`intent-contract: ${findings.length} finding(s) - see ${relative(PROJECT, OUT)}`);
process.exit(findings.length === 0 ? 0 : 1);
