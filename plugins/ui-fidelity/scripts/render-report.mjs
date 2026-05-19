#!/usr/bin/env node
// Merge .ui-fidelity/findings/*.json into report.json + report.md.
import { readFileSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const PROJECT = process.cwd();
const DIR = join(PROJECT, '.ui-fidelity', 'findings');
const OUT_JSON = join(PROJECT, '.ui-fidelity', 'report.json');
const OUT_MD = join(PROJECT, '.ui-fidelity', 'report.md');

const gates = {};
let totalFindings = 0;

if (existsSync(DIR)) {
  for (const f of readdirSync(DIR)) {
    if (!f.endsWith('.json')) continue;
    const gate = f.replace(/\.json$/, '');
    try {
      const data = JSON.parse(readFileSync(join(DIR, f), 'utf-8'));
      gates[gate] = data;
      totalFindings += (data.findings ?? []).length;
    } catch (e) {
      gates[gate] = { pass: null, error: String(e), findings: [] };
    }
  }
}

const overallPass = Object.values(gates).every((g) => g.pass !== false);

const report = {
  ran_at: new Date().toISOString(),
  pass: overallPass,
  total_findings: totalFindings,
  gates,
};
writeFileSync(OUT_JSON, JSON.stringify(report, null, 2));

let md = `# UI Fidelity Audit Report\n\n`;
md += `**Result:** ${overallPass ? 'PASS' : 'FAIL'} · **Findings:** ${totalFindings} · **Ran:** ${report.ran_at}\n\n`;
md += `## Gates\n\n| Gate | Pass | Findings |\n|------|------|----------|\n`;
for (const [name, g] of Object.entries(gates)) {
  const status = g.pass === true ? '✅' : g.pass === false ? '❌' : '⚠️';
  md += `| ${name} | ${status} | ${(g.findings ?? []).length} |\n`;
}
md += `\n## Findings\n\n`;
for (const [name, g] of Object.entries(gates)) {
  if (!g.findings || g.findings.length === 0) continue;
  md += `### ${name}\n\n`;
  for (const f of g.findings) {
    md += `- **[${f.severity ?? '?'}]** `;
    if (f.file) md += `\`${f.file}\` `;
    if (f.route) md += `route \`${f.route}\` `;
    if (f.element) md += `element "${f.element}" `;
    if (f.kind) md += `(kind: ${f.kind}) `;
    md += `\n  - why: ${f.why ?? ''}\n`;
    if (f['fix-hint']) md += `  - fix: ${f['fix-hint']}\n`;
  }
  md += `\n`;
}
writeFileSync(OUT_MD, md);

console.log(`report: ${overallPass ? 'PASS' : 'FAIL'} · ${totalFindings} findings`);
console.log(`  json: ${OUT_JSON}`);
console.log(`  md:   ${OUT_MD}`);
process.exit(overallPass ? 0 : 1);
