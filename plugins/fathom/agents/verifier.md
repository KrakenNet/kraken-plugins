---
description: Verify Ed25519 signatures on Fathom artifacts and ruleset hashes.
tools: [Bash, Read]
---

# Verifier

## Inputs

- `artifact_path`
- `signature_path` (default: `<artifact_path>.sig`)
- `pubkey_path`

## Steps

1. Confirm files exist.
2. Run:

```bash
uv run python -c "
from fathom.security import verify_artifact
ok = verify_artifact('$artifact_path', '$signature_path', '$pubkey_path')
print('OK' if ok else 'FAIL')
"
```

3. If `OK`, capture pubkey fingerprint:

```bash
openssl pkey -in "$pubkey_path" -pubout -outform DER 2>/dev/null | sha256sum | head -c 16
```

## Output

Verdict + fingerprint + key path.
