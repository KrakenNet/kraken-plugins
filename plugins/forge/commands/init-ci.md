---
description: Install Phase 3 GitHub Actions workflow — ensemble reviewers, E2E gauntlet, PR formatter, auto-fixer.
allowed-tools: [Bash, Read, Write]
---

# /forge:init-ci

Copies workflow template into `.github/workflows/forge-review.yml`.

## Preflight

```bash
[ -d .github ] || mkdir -p .github/workflows
[ -f .github/workflows/forge-review.yml ] && {
  echo "forge-review.yml exists. Aborting (use --force to overwrite)."
  exit 1
}
```

## Install

```bash
cp "${CLAUDE_PLUGIN_ROOT}/templates/.github/workflows/forge-review.yml" .github/workflows/forge-review.yml
```

## Required Secrets

Print to user:

- `ANTHROPIC_API_KEY` — Claude Code action auth
- `GITHUB_TOKEN` — provided by Actions, used for PR comments

## Wire-Up

Workflow triggers on `pull_request: [opened, synchronize]`. Jobs:

- `anti-cheat` — runs `anti-cheat-scan.sh full --strict` (FORGE_ANTI_CHEAT_STRICT=1).
  Strict semantics: `expires_at` ignored, YAML allowlist entries require a
  `STRICT_OK:` prefix on `reason:`, SHA-keyed `scaffolded-stubs.json`
  entries still apply (state-justified). Auto-degrades to lenient if any
  `prd.json` task still has `passes:false`.
- `security-review` — OWASP / injection scan
- `perf-review` — Big-O / memory leak scan
- `arch-review` — drift from `.forge/shared.md`
- `e2e-gauntlet` — staging container + Playwright suite
- `ci-autofixer` — on any job failure, reads logs, opens patch PR
- `specum-formatter` — on all green, rewrites PR body with diffs

## Local vs CI gate

| Surface | Mode | Why |
|---|---|---|
| PostToolUse hook | lenient | dev ergonomics during scaffold |
| Ralph Loop gate (`anti-cheat-scan.sh full`) | lenient | Phase 2 stubs still exist |
| `/forge:status` preview | lenient + strict (dual) | shows what would break on PR |
| CI job (`anti-cheat`) | strict | gates merge; ignores time-bombed allowlist entries |

## Report

Print install location, secrets needed, link to template for customization.
