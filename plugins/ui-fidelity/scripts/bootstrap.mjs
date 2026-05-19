#!/usr/bin/env node
// Bootstrap .ui-fidelity/ in the current project. Idempotent.
import { mkdirSync, writeFileSync, existsSync, copyFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const PLUGIN_ROOT = dirname(SCRIPT_DIR);
const PROJECT_ROOT = process.cwd();
const TARGET = join(PROJECT_ROOT, '.ui-fidelity');

const DEFAULT_CONFIG = {
  gates: {
    'console-error':   { enabled: true },
    'dead-button':     { enabled: true },
    'orphan-route':    { enabled: true },
    'contrast':        { enabled: true, 'axe-tags': ['wcag2a', 'wcag2aa'] },
    'flow-continuity': { enabled: true },
    'intent-contract': { enabled: true },
    'persona-journey': { enabled: true },
    'llm-ux-critic':   {
      enabled: true,
      model: 'gemma3:latest',
      base: process.env.UI_FIDELITY_LLM_BASE || 'http://localhost:41001',
    },
  },
  budget: { 'llm-routes': 10, 'per-route-timeout-ms': 30000 },
  allow: {
    console: [],
    'orphan-routes': ['/', '/login', '/onboarding', '/onboarding/.*'],
  },
};

function w(p, content) {
  if (existsSync(p)) return false;
  writeFileSync(p, content);
  return true;
}

mkdirSync(TARGET, { recursive: true });
mkdirSync(join(TARGET, 'findings'), { recursive: true });
mkdirSync(join(TARGET, '.runner'), { recursive: true });
mkdirSync(join(TARGET, 'cache'), { recursive: true });

w(join(TARGET, 'config.json'), JSON.stringify(DEFAULT_CONFIG, null, 2) + '\n');
w(join(TARGET, 'console-allow.json'), '[]\n');
w(
  join(TARGET, 'orphan-allow.json'),
  JSON.stringify(DEFAULT_CONFIG.allow['orphan-routes'], null, 2) + '\n',
);

const TEMPLATES_SRC = join(PLUGIN_ROOT, 'templates');
const TEMPLATES_DST = join(TARGET, 'templates');
mkdirSync(TEMPLATES_DST, { recursive: true });
for (const f of readdirSync(TEMPLATES_SRC)) {
  const dst = join(TEMPLATES_DST, f);
  if (!existsSync(dst)) copyFileSync(join(TEMPLATES_SRC, f), dst);
}

w(join(TARGET, '.gitignore'), '.runner/\ncache/\nreport.json\nreport.md\nfindings/\n');

console.log(`ui-fidelity: bootstrapped ${TARGET}`);
console.log('next: run /ui-fidelity:intent --all to scaffold INTENT.md for every route');
console.log('then: /ui-fidelity:audit');
