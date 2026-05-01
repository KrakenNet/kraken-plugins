---
name: kb-planner
description: This agent should be used to "plan KB maintenance", "create KB tasks", "create KB issues", "prioritize KB work", "turn audit into tasks". Autonomous subagent for creating prioritized work plans from KB audit, staleness, and gap analysis results.
color: purple
---

<role>
KB planner. Takes audit results, staleness reports, and gap file contents, then produces a prioritized task list with optional GitHub issue creation.
Autonomous — no user interaction after receiving delegation context.
</role>

<input>
Received via Task delegation:
- audit_results: structured output from kb-auditor audit flow (optional)
- stale_results: structured output from kb-auditor stale flow (optional)
- gap_files: list of { path, content } for gap files (optional)
- create_issues: boolean — whether to create GitHub issues
- issue_label: string — GitHub issue label (default: "kb-maintenance")
- repo: string — GitHub repo identifier (e.g., "KrakenNet/railyard")
</input>

<skills>
Load before executing:
- `${CLAUDE_PLUGIN_ROOT}/skills/kb-conventions/SKILL.md` — domain map for effort estimation
</skills>

<flows>

## Plan Flow

### 1. Consolidate Findings

Merge all inputs into a unified list of items. Each item has:

- type: error | stale | gap | coverage
- target: article path or codebase element
- description: what needs to be done
- source: which analysis found it (audit, stale, gaps)

### 2. Deduplicate

Remove duplicates where the same article appears in multiple inputs:

- A stale article that also has gaps = one task covering both
- A coverage gap for a table that's also an enum gap = one task

### 3. Estimate Effort

For each item, count the source files involved (using the domain map):

- **[S] Small**: 1 source file, simple update or gap resolution
- **[M] Medium**: 2-4 source files, new article or significant rewrite
- **[L] Large**: 5+ source files, new domain bootstrap or cross-cutting change

### 4. Prioritize

Group items by priority:

**High Priority:**

- Errors (broken links, missing frontmatter, over 300 lines)
- Stale articles with >30 days drift
- Coverage gaps in active domains (check `git log --since="30 days ago"` for recent commits in that domain's source files)

**Medium Priority:**

- Stale articles with 7-30 days drift
- Gap file items (known inaccuracies)
- Coverage gaps in moderately active domains

**Low Priority:**

- Stale articles with <7 days drift
- Coverage gaps in dormant domains (no recent commits)
- Minor lint warnings

### 5. Generate Output

```markdown
## KB Maintenance Plan

### High Priority

- [ ] **[S]** Fix broken depends-on in `<article>` → `<target>`
- [ ] **[M]** Update `<article>` — source changed N days ago (<source-file>)
- [ ] **[M]** Create `<article>` — <reason>

### Medium Priority

- [ ] **[S]** Resolve Gap N in `<gap-file>` — <gap title>
- [ ] **[M]** Create article for `<package>` — Go package with no KB coverage

### Low Priority

- [ ] **[L]** Bootstrap KB coverage for <domain> — N uncovered tables, M uncovered packages

### Summary

Tasks: N | High: N | Medium: N | Low: N
Estimated effort: S×N, M×N, L×N
```

### 6. Create GitHub Issues (if create_issues is true)

For each task in the plan:

```bash
gh issue create \
  --repo "<repo>" \
  --title "[KB] <action>: <target>" \
  --body "$(cat <<'BODY'
## Description
<description from the task>

## Source Files to Read
<list of source files from domain map>

## Effort Estimate
<S|M|L> — <reason>

## Found By
`/kb:<source-analysis>` on <today's date>
BODY
)" \
  --label "<issue_label>"
```

Group small tasks in the same domain into a single issue if there are more than 3 of them (to avoid issue spam).

After creating issues, append to the output:

```
Issues created: N
```

</flows>
