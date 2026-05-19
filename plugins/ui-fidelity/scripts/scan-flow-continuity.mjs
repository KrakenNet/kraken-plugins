#!/usr/bin/env node
// Static flow-continuity gate.
// For each route file: collect <input>/<textarea>/<select> value bindings and
// the primary CTA's onClick handler. Fail if the handler references none of
// the inputs.
//
// No AST library required - we use targeted regex which suffices for the
// common JSX patterns. False negatives are accepted; false positives are
// rare and surface as warnings.
import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const PROJECT = process.cwd();
const OUT = join(PROJECT, '.ui-fidelity', 'findings', 'flow-continuity.json');

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

function collectInputs(src) {
  const inputs = [];
  const re1 = /<(input|textarea|select)\b[^>]*value=\{([^}]+)\}[^>]*onChange=\{([^}]+)\}/g;
  let m;
  while ((m = re1.exec(src)) != null) {
    inputs.push({ tag: m[1], valueBinding: m[2].trim(), onChange: m[3].trim() });
  }
  const re2 = /<(input|textarea|select)\b[^>]*onChange=\{([^}]+)\}[^>]*value=\{([^}]+)\}/g;
  while ((m = re2.exec(src)) != null) {
    inputs.push({ tag: m[1], valueBinding: m[3].trim(), onChange: m[2].trim() });
  }
  return inputs;
}

function bindingTokens(binding) {
  const ids = binding.match(/[A-Za-z_$][\w$]*/g) ?? [];
  return new Set(ids.filter((t) => !['true', 'false', 'null', 'undefined'].includes(t)));
}

function findPrimaryCTA(src) {
  let m = src.match(/<(button|a)[^>]*data-cta=["'`]primary["'`][^>]*onClick=\{([^}]+)\}/);
  if (m) return { handler: m[2].trim(), kind: 'data-cta=primary' };

  const formMatch = src.match(/<form[^>]*onSubmit=\{([^}]+)\}/);
  if (formMatch && /<button[^>]*type=["'`]submit["'`]/.test(src)) {
    return { handler: formMatch[1].trim(), kind: 'submit' };
  }

  const re = /<button[^>]*onClick=\{([^}]+)\}[^>]*>([\s\S]*?)<\/button>/g;
  while ((m = re.exec(src)) != null) {
    const text = m[2].replace(/<[^>]+>/g, '').trim();
    if (/^(build|create|save|submit|send|run|publish|generate|start)\b/i.test(text)) {
      return { handler: m[1].trim(), kind: `verb:${text.split(/\s+/)[0]}` };
    }
  }
  return null;
}

function resolveHandlerBody(src, handler) {
  let name = handler.replace(/^\(\s*\)\s*=>\s*/, '').replace(/^\s*\(\s*e\s*\)\s*=>\s*/, '').trim();
  name = name.replace(/^void\s+/, '').replace(/\(.*\)$/, '');
  let m = src.match(new RegExp(`function\\s+${name}\\s*\\([^)]*\\)\\s*\\{([\\s\\S]*?)\\n\\s{0,4}\\}`));
  if (m) return m[1];
  m = src.match(new RegExp(`const\\s+${name}\\s*=\\s*(?:async\\s*)?\\([^)]*\\)\\s*=>\\s*\\{([\\s\\S]*?)\\n\\s{0,4}\\}`));
  if (m) return m[1];
  m = src.match(new RegExp(`const\\s+${name}\\s*=\\s*(?:async\\s*)?\\([^)]*\\)\\s*=>\\s*([^;\\n]+)`));
  if (m) return m[1];
  return handler;
}

const SRC = join(PROJECT, 'src');
if (!existsSync(SRC)) {
  writeFileSync(OUT, JSON.stringify({ pass: null, error: 'src/ not found', findings: [] }, null, 2));
  process.exit(0);
}

const files = walk(SRC);
const findings = [];

for (const file of files) {
  const src = readFileSync(file, 'utf-8');
  const inputs = collectInputs(src);
  if (inputs.length === 0) continue;
  const cta = findPrimaryCTA(src);
  if (cta == null) continue;
  const body = resolveHandlerBody(src, cta.handler);
  const bodyTokens = new Set(body.match(/[A-Za-z_$][\w$]*/g) ?? []);
  const referenced = inputs.some((inp) => {
    const tokens = bindingTokens(inp.valueBinding);
    for (const t of tokens) if (bodyTokens.has(t)) return true;
    return false;
  });
  if (!referenced) {
    findings.push({
      gate: 'flow-continuity',
      severity: 'error',
      file: relative(PROJECT, file),
      inputs: inputs.map((i) => ({ tag: i.tag, value: i.valueBinding })),
      cta,
      why: 'primary CTA handler does not reference any input value binding; user input is dropped on click',
      'fix-hint': 'thread the input state into the CTA handler (navigate state, fetch body, or function arg)',
    });
  }
}

writeFileSync(OUT, JSON.stringify({ pass: findings.length === 0, findings }, null, 2));
console.log(`flow-continuity: ${findings.length} finding(s) - see ${relative(PROJECT, OUT)}`);
process.exit(findings.length === 0 ? 0 : 1);
