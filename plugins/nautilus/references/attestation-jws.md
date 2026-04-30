# Nautilus Attestation Envelope (Ed25519 JWS)

Every successful broker request emits a signed attestation token over the request's identity, scope, and decision metadata. The token uses the JWS compact serialization with Ed25519.

## Format

Compact serialization, three base64url-encoded segments joined by `.`:

```
<header>.<payload>.<signature>
```

Example (line-broken for readability):

```
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.
eyJyZXF1ZXN0X2lkIjoicmVxLTAxIiwiYWdlbnRfaWQiOiJhZ2VudC1mb28iLC4uLn0.
3kP...signature_bytes_base64url...
```

## Header

```json
{"alg": "EdDSA", "typ": "JWT"}
```

`alg` is always `EdDSA` (Ed25519). `typ` is `JWT` (the envelope is a JWT-shaped JWS).

## Payload Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `request_id` | string (UUID) | yes | Globally unique request identifier. |
| `agent_id` | string | yes | Caller identity passed to `broker.request()`. |
| `intent` | string | yes | Free-form intent string supplied by the caller. |
| `sources_queried` | list[string] | yes | Source IDs the broker actually queried. |
| `sources_denied` | list[string] | yes | Source IDs the broker refused (rule pack denial, classification mismatch, disabled, etc.). |
| `classification` | string | yes | Effective classification of the response (max of queried sources). One of `unclassified`, `confidential`, `secret`, `top_secret`. |
| `decision` | string | yes | `allow`, `partial`, or `deny`. |
| `timestamp` | string (RFC3339) | yes | UTC timestamp of decision, e.g. `2026-04-30T12:34:56Z`. |
| `cost_caps` | object | no | `{enforced: true, max_tokens: ..., observed_tokens: ...}` summary if cost caps were active. |
| `fact_set_hash` | string (hex) | no | SHA-256 of the canonicalized response rows. Lets downstream verifiers check data integrity. |
| `ingest_integrity_status` | string | no | `clean`, `quarantined`, `anomaly` — surfaces ingest-integrity findings into the attestation. |

## Verification Pseudocode

```python
import base64, json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def verify_attestation(token: str, pubkey_pem: bytes) -> dict:
    """Verify a Nautilus attestation JWS. Returns the decoded payload on success."""
    header_b64, payload_b64, sig_b64 = token.split(".")
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = _b64url_decode(sig_b64)

    pubkey = Ed25519PublicKey.from_public_bytes(_pem_to_raw(pubkey_pem))
    try:
        pubkey.verify(signature, signing_input)
    except InvalidSignature:
        raise ValueError("attestation signature invalid")

    header = json.loads(_b64url_decode(header_b64))
    if header.get("alg") != "EdDSA":
        raise ValueError(f"unexpected alg: {header.get('alg')}")

    payload = json.loads(_b64url_decode(payload_b64))
    return payload
```

A complete implementation also validates `timestamp` freshness and checks `decision`/`classification` against the caller's policy.

## Pubkey Distribution

The broker exposes its current attestation public key at:

```
GET ${NAUTILUS_URL}/v1/pubkey
```

Response: `application/x-pem-file` (PEM-encoded Ed25519 SubjectPublicKeyInfo).

### Fingerprint

The pubkey fingerprint is `sha256(DER pubkey)`, hex-encoded:

```python
import hashlib
from cryptography.hazmat.primitives import serialization

def fingerprint(pubkey_pem: bytes) -> str:
    pub = serialization.load_pem_public_key(pubkey_pem)
    der = pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return hashlib.sha256(der).hexdigest()
```

Operators should pin the fingerprint out-of-band (config management, secrets vault) and reject responses signed by unrecognized keys.

### Key Rotation

When the broker rotates keys, it serves the new key at `/v1/pubkey` and continues to accept verification of tokens issued under the previous key for the configured grace window. Verifiers SHOULD cache and refresh the pubkey on signature failure.
