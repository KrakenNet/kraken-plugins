---
description: Start a Gauntlet Loop — capture the goal, pick the domain, write .gauntlet/charter.md, then hand off to /gauntlet:bar.
argument-hint: "<goal>" [--domain agentic|rl|coding|other]
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, Agent]
---

# /gauntlet:new

Set up a run. Read `${CLAUDE_PLUGIN_ROOT}/skills/gauntlet-loop/SKILL.md` first.

## 1. Capture the goal

Take `$ARGUMENTS` as the goal. Make it ambitious and make it a *destination* — what should exist when
this is done, not how to build it. If the user handed you an implementation plan, say so and offer
the destination form instead; the loop works worse when you replace the model's judgment with an
outline.

Do **not** decompose here. That is the lead's job in `/gauntlet:run`.

## 2. Domain

From `--domain`, or infer, or ask once with `AskUserQuestion`:

- `agentic` — agent capabilities: tool use, recovery, planning, stopping → `references/bars-agentic.md`
- `rl` — reinforcement learning: policies, rewards, returns, curves → `references/bars-rl.md`
- `coding` — general software → `references/bars-coding.md`
- `other` — anything inspectable; use the closest recipe as a template

## 3. Constraints worth asking about

Only ask what actually changes the run, in one `AskUserQuestion` batch:

- Any reference the user already has in mind for the bar (a real artifact beats anything you'd find)
- Compute or budget ceiling — this decides how long the loop runs, and it is the usual stop condition
- Anything off-limits (files, services, spend, network)

## 4. Write the charter

```bash
mkdir -p .gauntlet/work
```

Write `.gauntlet/charter.md`:

```markdown
# Goal
<the destination, in the user's terms>

# Domain
<agentic | rl | coding | other>

# Constraints
<what is off-limits, budget ceiling>

# Stop condition
<what makes the user stop the run — not a round count>
```

Add `.gauntlet/` to `.gitignore` unless the user wants the receipts committed. Ask if it is unclear;
the ledger is often worth keeping.

## 5. Hand off

Tell the user the loop cannot start without a sound bar, then run `/gauntlet:bar`.
