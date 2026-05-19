#!/usr/bin/env node
// Detect routes registered in App.tsx that no Link or navigate(...) call references
// from outside their own subtree. Writes .ui-fidelity/findings/orphan-route.json.
import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, resolve, relative, dirname } from 'node:path';

const PROJECT = process.cwd();
const APP_TSX = join(PROJECT, 'src', 'App.tsx');
const OUT = join(PROJECT, '.ui-fidelity', 'findings', 'orphan-route.json');
const ALLOW_FILE = join(PROJECT, '.ui-fidelity', 'orphan-allow.json');

if (!existsSync(APP_TSX)) {
  writeFileSync(OUT, JSON.stringify({ pass: null, error: 'src/App.tsx not found', findings: [] }, null, 2));
  process.exit(0);
}

const app = readFileSync(APP_TSX, 'utf-8');
const routeRe = /<Route\s+path=["'`]([^"'`]+)["'`][^>]*element=\{[^}]*?<(\w+)/g;
const routes = [];
for (const m of app.matchAll(routeRe)) routes.push({ path: m[1], component: m[2] });

const allow = existsSync(ALLOW_FILE) ? JSON.parse(readFileSync(ALLOW_FILE, 'utf-8')) : [];
function allowed(p) {
  return allow.some((rule) => new RegExp('^' + rule.replace(/\*/g, '.*') + '$').test(p));
}

function walk(dir, out = []) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) {
      if (entry === 'node_modules' || entry.startsWith('.')) continue;
      walk(full, out);
    } else if (/\.(tsx?|jsx?)$/.test(entry)) {
      out.push(full);
    }
  }
  return out;
}

const SRC = join(PROJECT, 'src');
const files = walk(SRC);

function findRouteFile(component) {
  for (const f of files) {
    const txt = readFileSync(f, 'utf-8');
    if (new RegExp(`export\\s+(function|const)\\s+${component}\\b`).test(txt)) return f;
  }
  return null;
}

function searchExternal(routePath, routeFile) {
  const routeDir = routeFile ? dirname(routeFile) : null;
  const escaped = routePath.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const linkRe = new RegExp(`<Link[^>]*to=["'\`]${escaped}\\b`);
  const navRe  = new RegExp(`navigate\\(\\s*["'\`]${escaped}\\b`);
  const tmplRe = new RegExp(`["'\`]${escaped}\\$\\{`);
  for (const f of files) {
    if (routeDir && f.startsWith(routeDir + '/')) continue;
    if (routeDir && f === routeFile) continue;
    const txt = readFileSync(f, 'utf-8');
    if (linkRe.test(txt) || navRe.test(txt) || tmplRe.test(txt)) {
      return f;
    }
  }
  return null;
}

const findings = [];
for (const r of routes) {
  if (allowed(r.path)) continue;
  if (r.path.includes(':')) continue; // dynamic-only; not orphan-checkable
  const file = findRouteFile(r.component);
  const linker = searchExternal(r.path, file);
  if (linker == null) {
    findings.push({
      gate: 'orphan-route',
      severity: 'error',
      route: r.path,
      file: file ? relative(PROJECT, file) : null,
      why: `no Link or navigate(${r.path}) outside its own subtree`,
      'fix-hint': 'add a Link from the shell nav, the persona home, or a relevant index page',
    });
  }
}

writeFileSync(OUT, JSON.stringify({ pass: findings.length === 0, findings }, null, 2));
console.log(`orphan-route: ${findings.length} finding(s) — see ${relative(PROJECT, OUT)}`);
process.exit(findings.length === 0 ? 0 : 1);
