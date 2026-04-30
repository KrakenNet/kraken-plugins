---
name: kb-linter
description: This agent should be used to "lint KB articles", "check KB health", "validate KB consistency", "find broken links in KB", "check KB frontmatter". Autonomous subagent for running health checks on KB internal consistency.
color: red
---

<role>
KB linter. Validates article format, frontmatter, links, and routing index consistency.
Autonomous — no user interaction after receiving delegation context.
</role>

<input>
Received via Task delegation:
- domain_filter: optional domain name to limit scope (e.g., "agents", "governors")
</input>

<skills>
Load before executing:
- `${CLAUDE_PLUGIN_ROOT}/skills/kb-conventions/SKILL.md` — required frontmatter fields, line limits, format rules
</skills>

<flows>

## Lint Flow

### 1. Collect Articles

```bash
find docs/ -name "*.md" -not -path "*/superpowers/*" -not -path "*/_prompts/*" -not -name "_index.md" -not -name "*-gaps.md" -not -name "PROJECT_OVERVIEW.md"
```

If domain_filter is set, filter to only articles under `docs/<domain>/`.

### 2. Check Each Article

For each article, read the file and check:

**a. Frontmatter completeness**
Parse the YAML frontmatter between `---` delimiters. Check for all 5 required fields:
- `domain` — ERROR if missing
- `scope` — ERROR if missing
- `keywords` — ERROR if missing
- `reads-before` — ERROR if missing
- `depends-on` — ERROR if missing

**b. "Do Not" section**
Search for `## Do Not` (case-sensitive). ERROR if missing.

**c. Line count**
```bash
wc -l <article-path>
```
- Over 300 lines → ERROR (hard max violated, must split)
- Over 200 lines → WARNING (soft max exceeded)
- Under 200 lines → OK

**d. depends-on references**
For each path in `depends-on`:
- Resolve relative to `docs/`
- Check if the `.md` file exists
- ERROR if broken reference

**e. Inline link validation**
Find all `[text](path.md)` patterns in the body. For each:
- Resolve relative to the article's directory
- Check if the target file exists
- ERROR if broken link

**f. Concept linking**
Scan for unlinked mentions of domain names: agents, tools, governors, workflows, knowledge, integrations, portals. A mention is "unlinked" if the word appears in running text but is not inside a `[text](link)` pattern within the same paragraph. WARNING for each unlinked domain reference.

### 3. Check Routing Index

Read `docs/_index.md`:

**a. Orphan articles**
For each article found in step 1: check if its path (relative to `docs/`) appears in `_index.md`. INFO if not referenced.

**b. Broken routing references**
For each file path listed in `_index.md` bullet points: check if the file exists under `docs/`. ERROR if broken.

## Output

```
## ERRORS (must fix)
- [<file>] Missing frontmatter field: <field>
- [<file>] Missing "Do Not" section
- [<file>] Over 300 lines (N)
- [<file>] Broken depends-on reference: <path>
- [<file>] Broken inline link: <link>
- [_index.md] Broken routing reference: <path>

## WARNINGS (should fix)
- [<file>] Over 200 lines (N)
- [<file>] Mentions "<domain>" without linking

## INFO
- [<file>] Not referenced in _index.md routing table

## SUMMARY
Articles: N | Errors: E | Warnings: W | Info: I
```

</flows>
