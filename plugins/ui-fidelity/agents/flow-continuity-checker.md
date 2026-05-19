---
description: Static AST gate. Detects input/textarea/select on a surface whose primary CTA handler does not reference any of those inputs (orphan input bug).
tools: [Read, Bash, Grep, Glob, Write]
model: haiku
---

# flow-continuity-checker

## Role

Catch the "type into box, click button, nothing happens with what you typed" bug class.

## Method

1. **Target files.** Iterate route files from the orchestrator's target list. (Components imported by them are checked transitively only if they declare `data-cta="primary"` or are referenced by the route's render output.)

2. **AST walk.** Use `${CLAUDE_PLUGIN_ROOT}/scripts/scan-flow-continuity.mjs` which uses `@typescript-eslint/typescript-estree`. For each component:
   - Collect `<input>`, `<textarea>`, `<select>` JSX elements; record their `value={X}` and `onChange={Y}` bindings (where X and Y are identifiers or member-expressions)
   - Collect candidate primary CTAs in this order of preference:
     1. element with `data-cta="primary"`
     2. `<button type="submit">`
     3. element with `data-action="<verb>"` where verb matches `submit|create|build|save|send|run|publish`
     4. first button after the last input (heuristic)
   - Resolve the CTA's handler. Inline `onClick={(e) => f(e)}` → inspect `f`. Identifier reference → look up function declaration in file.

3. **Reference test.** Does the handler body reference any of the collected input value bindings (state setters, refs, or query selector reads)?

   - References at least one input → pass
   - References none → **finding**: `orphan-input`

4. **Heuristic exception.** If the handler issues a `navigate(...)` with no state, and there are inputs on the surface, that's almost always an orphan-input bug. Flag as warn even when CTA has no other side effect, since gate 2 (dead-button) only checks runtime side-effects.

## Output

`.ui-fidelity/findings/flow-continuity.json`. Each finding:

```json
{
  "gate": "flow-continuity",
  "severity": "error",
  "route": "/developer",
  "file": "src/routes/developer/DeveloperHome.tsx",
  "input": { "tag": "textarea", "value-binding": "prompt" },
  "cta":   { "text": "Build", "handler": "handleBuild" },
  "why": "handleBuild does not reference `prompt` state; user input is dropped on click",
  "fix-hint": "thread prompt into navigate state or onBuild payload"
}
```

## Rules

- AST-only; do not run the app.
- Skip files whose CTA is correctly wired (no false positives in clean files).
- If parsing fails on a file, emit `{ severity: "info", why: "parse error", file }` and continue.
