---
description: LLM-as-critic UX pass on a route. Screenshots + DOM + INTENT.md → adversarial findings JSON.
argument-hint: <route> [--model <id>] [--base <url>]
allowed-tools: [Bash, Read, Write, Agent]
---

# /ui-fidelity:critic

Cheap LLM critique. Gate 8 only — useful as a fast pre-commit check.

## Args

- `<route>` (required) — URL path or route file
- `--model <id>` — model id (default `gemma3:latest`)
- `--base <url>` — LLM base (default `$UI_FIDELITY_LLM_BASE` or `http://localhost:41001`)

## Process

1. Locate sibling `INTENT.md` (error if missing — instruct user to run `/ui-fidelity:intent`)
2. Locate Playwright config; start dev server if not running
3. Screenshot route at 1440x900 + capture DOM text+roles
4. Dispatch `ui-fidelity:llm-ux-critic` agent with screenshot path, DOM snippet, INTENT.md content, model, base
5. Print findings table sorted by severity. Exit non-zero if any `error` or `warn` finding.

## Cost note

Single route → one LLM call. Cheap. Use during dev. Full-codebase critic happens inside `/ui-fidelity:audit` (gate 8).
