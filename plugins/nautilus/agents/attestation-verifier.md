---
description: Verify Nautilus JWS attestations and walk audit chains.
tools: [Bash, Read]
---

# Attestation Verifier

## Inputs

- `token` (JWS string)
- `pubkey_path` (default fetched from broker `/v1/pubkey` if exposed)

## Steps

1. Split `header.payload.signature` on `.`.
2. Base64-decode header; confirm alg=EdDSA, typ=JWT.
3. Verify with pubkey:

```bash
uv run python -c "
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature
import base64, sys, json
hdr_b64, pl_b64, sig_b64 = '$token'.split('.')
def b64u(s): return base64.urlsafe_b64decode(s + '==')
key = load_pem_public_key(open('$pubkey_path','rb').read())
try:
    key.verify(b64u(sig_b64), (hdr_b64+'.'+pl_b64).encode())
    print('OK')
    print(json.dumps(json.loads(b64u(pl_b64)), indent=2))
except InvalidSignature:
    print('FAIL')
    sys.exit(1)
"
```

## Output

Verdict + decoded payload preview.
