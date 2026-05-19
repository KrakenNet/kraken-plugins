#!/usr/bin/env node
// LLM-as-critic: feed a screenshot + DOM + INTENT.md to an OpenAI-compatible
// chat completions endpoint and emit findings.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join, basename } from 'node:path';

const args = Object.fromEntries(
  process.argv.slice(2).map((a) => {
    const m = a.match(/^--([^=]+)=(.*)$/);
    return m ? [m[1], m[2]] : [a.replace(/^--/, ''), true];
  }),
);

const route = args.route;
const screenshot = args.screenshot;
const domPath = args.dom;
const intentPath = args.intent;
const base = args.base || process.env.UI_FIDELITY_LLM_BASE || 'http://localhost:41001';
const model = args.model || 'gemma3:latest';

if (!route || !screenshot || !intentPath) {
  console.error('usage: llm-critic.mjs --route=/path --screenshot=<png> --dom=<json> --intent=<md>');
  process.exit(2);
}

const intent = existsSync(intentPath) ? readFileSync(intentPath, 'utf-8') : '';
const dom = existsSync(domPath) ? readFileSync(domPath, 'utf-8') : '';
const img = readFileSync(screenshot).toString('base64');

const system = `You are an adversarial UX critic. Given a persona, primary goal, and a rendered page, list:
(a) dead-ends, (b) redundant or off-persona CTAs, (c) label/behavior mismatches, (d) missing primary path, (e) orphan inputs.
Be specific. Cite element text and role. Output STRICT JSON only:
{ "findings": [{ "severity": "error"|"warn"|"info", "kind": "dead-end"|"redundant-cta"|"off-persona"|"label-behavior-mismatch"|"orphan-input"|"missing-primary"|"density", "element": "<short text>", "why": "<one sentence>", "fix-hint": "<imperative>" }] }`;

const user = `Route: ${route}

INTENT.md:
${intent}

DOM snapshot:
${dom.slice(0, 6000)}

Screenshot is attached.`;

const body = {
  model,
  messages: [
    { role: 'system', content: system },
    {
      role: 'user',
      content: [
        { type: 'text', text: user },
        { type: 'image_url', image_url: { url: `data:image/png;base64,${img}` } },
      ],
    },
  ],
  temperature: 0,
};

const res = await fetch(`${base}/v1/chat/completions`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});

if (!res.ok) {
  const txt = await res.text();
  console.error(`llm-critic: ${res.status}: ${txt}`);
  process.exit(1);
}

const data = await res.json();
const content = data.choices?.[0]?.message?.content ?? '';
const jsonMatch = content.match(/\{[\s\S]*\}/);
let parsed = { findings: [] };
if (jsonMatch) {
  try {
    parsed = JSON.parse(jsonMatch[0]);
  } catch {
    parsed = { findings: [{ severity: 'info', kind: 'parse-error', element: '', why: 'critic did not return valid JSON', 'fix-hint': content.slice(0, 200) }] };
  }
}

const enriched = (parsed.findings ?? []).map((f) => ({
  gate: 'llm-ux-critic',
  route,
  intent: basename(intentPath),
  ...f,
}));

const outDir = join(process.cwd(), '.ui-fidelity', 'findings');
const outFile = join(outDir, 'llm-ux-critic.json');
let existing = { findings: [] };
if (existsSync(outFile)) {
  try { existing = JSON.parse(readFileSync(outFile, 'utf-8')); } catch { /* empty */ }
}
const merged = [...(existing.findings ?? []), ...enriched];
writeFileSync(outFile, JSON.stringify({ pass: merged.every((f) => f.severity !== 'error'), findings: merged }, null, 2));

console.log(`llm-ux-critic: ${enriched.length} finding(s) for ${route}`);
