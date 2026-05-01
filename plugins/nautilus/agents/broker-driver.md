---
description: Driver for Nautilus broker REST API — request, sources, caps. Builds bodies, parses envelope, surfaces attestation.
tools: [Bash, Read, Write]
---

# Broker Driver

## Inputs

- Action: request | sources-list | sources-enable | sources-disable | caps-show
- Action-specific args.
- `NAUTILUS_URL`, `NAUTILUS_TOKEN`.

## Steps

1. Build body per action.
2. curl with `-H "Authorization: Bearer ${NAUTILUS_TOKEN}" -H "Content-Type: application/json"`.
3. Parse envelope.
4. For request: pretty-print attestation header (alg=EdDSA), data summary, denied sources.

## Output

Compact markdown block.
