---
description: Create a new KB article — interactive by default, or autonomous with --quick
argument-hint: [domain/scope] [--quick]
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, Agent]
---

# KB New Article

Create a new Knowledge Base article for the Railyard project.

## Parse Arguments

From `$ARGUMENTS`:
- **Positional**: `[domain/scope]` (e.g., `agents/skills`, `governors/runtime`)
- **--quick**: Autonomous mode — skip interactive questions, generate from source code

## Route by Mode

### Interactive (default)

Ask these questions one at a time:

1. **"Which domain does this article cover?"**
   Options: agents, tools, governors, workflows, knowledge, integrations, ml, platform, portals
   (Skip if domain was provided positionally)

2. **"What scope or aspect does this article cover?"**
   Examples: overview, execution, runtime, configuration, etc.
   (Skip if scope was provided positionally)

3. **"Which source files should I read to write this article?"**
   Suggest files from the domain map (see kb-conventions skill). Let the user add or remove from the list.

4. **"Any specific things to cover or exclude?"**
   Free-form notes. Optional — user can skip.

Construct the article path: `docs/<domain>/<scope>.md`

Check if the file already exists:
```bash
test -f docs/<domain>/<scope>.md && echo "EXISTS" || echo "NEW"
```
If EXISTS: warn the user and ask if they want to update instead (delegate to /kb:update).

### Quick (--quick)

1. Parse domain and scope from the positional argument (e.g., `agents/skills` → domain=agents, scope=skills)
2. If not provided, error: "Usage: /kb:new <domain/scope> --quick"
3. Look up source files from the domain map in kb-conventions skill
4. Construct article path: `docs/<domain>/<scope>.md`
5. Check if file exists — error if it does: "Article already exists. Use /kb:update instead."

## Delegate

Delegate to `kb-writer` agent via Agent tool with:
- action: create
- article_path: `<domain>/<scope>.md`
- domain: `<domain>`
- source_files: list of source file paths
- scope: `<scope>`
- user_notes: any notes from the interactive flow (or empty for --quick)

## Report

Show the agent's output summary to the user. Include:
- Path to the created article
- Line count
- Whether _index.md was updated
- Whether a gap file was created
