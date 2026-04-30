---
description: Turn KB audit, staleness, and gap analysis into a prioritized task list with optional GitHub issues
argument-hint: [--source audit|stale|gaps|all] [--domain <domain>] [--issues] [--label <label>]
allowed-tools: [Bash, Read, Glob, Grep, Agent]
---

# KB Plan

Generate a prioritized maintenance plan from KB analysis results, optionally creating GitHub issues.

## Parse Arguments

From `$ARGUMENTS`:
- **--source**: which analysis to plan from — `audit`, `stale`, `gaps`, or `all` (default: `all`)
- **--domain**: limit scope to one domain
- **--issues**: also create GitHub issues
- **--label**: GitHub issue label (default: `kb-maintenance`)

## Gather Analysis Results

Run the relevant analysis by delegating to existing agents:

### If source = audit or all
Delegate to `kb-auditor` agent with action=audit, domain_filter if set.
Capture the structured gap report.

### If source = stale or all
Delegate to `kb-auditor` agent with action=stale, domain_filter if set.
Capture the staleness report.

### If source = gaps or all
Find and read all gap files:
```bash
find docs/ -name "*-gaps.md" -not -path "*/superpowers/*" | sort
```
If domain filter is set, filter to `docs/<domain>/`.
Read each gap file and collect { path, content }.

Run audit and stale in parallel when both are needed.

## Detect Repo

If `--issues` is set, detect the GitHub repo:
```bash
gh repo view --json nameWithOwner -q .nameWithOwner
```

## Delegate

Delegate to `kb-planner` agent via Agent tool with:
- audit_results: from audit analysis (or null)
- stale_results: from stale analysis (or null)
- gap_files: list of { path, content } (or null)
- create_issues: true if --issues flag set
- issue_label: value of --label flag
- repo: detected repo identifier

## Report

Show the planner's prioritized task list to the user.
If issues were created, show the count and link to the issue list.
