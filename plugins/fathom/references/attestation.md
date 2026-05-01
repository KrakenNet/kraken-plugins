# Attestation

Fathom evaluations can be cryptographically attested. The engine, when
constructed with an `AttestationService`, signs each `EvaluationResult` and
returns a JWT alongside the decision. The token is portable proof that a
specific Fathom instance produced a specific decision on a specific input,
and survives leaving the box that produced it.

For the local audit log (always-on, signature-independent) see the fathom
source repo's `concepts/audit-attestation.md`. This page documents the
on-the-wire envelope.

## JWS envelope

JWT compact serialization, three base64url segments separated by dots:

```
<header>.<payload>.<signature>
```

## Header

```json
{ "alg": "EdDSA", "typ": "JWT" }
```

`EdDSA` is PyJWT's name for Ed25519-over-JWT. Ed25519 was chosen for compact
signatures (64 bytes), fast verification, and a small enough public-key PEM
to embed in verifier images.

## Payload fields

| Field           | Type        | Description                                                                                       |
|-----------------|-------------|---------------------------------------------------------------------------------------------------|
| `iss`           | str         | Issuer identifier (e.g. `"fathom"` or a deployment-specific identity).                            |
| `sub`           | str         | Subject — the request id (typically the engine's session id for this evaluation).                  |
| `iat`           | int         | Issued-at timestamp, Unix seconds.                                                                |
| `exp`           | int         | Expiry, Unix seconds. Verifiers should reject tokens past `exp`.                                  |
| `decision`      | str         | The rule-engine output (`allow`, `deny`, `escalate`, etc.).                                       |
| `reason`        | str         | Human-readable explanation drawn from the firing rule's `reason:`.                                |
| `ruleset_hash`  | str (hex)   | sha256 of the compiled CLIPS source the engine loaded; binds the token to a specific rule set.    |
| `engine_version`| str         | Fathom version string (semver, matches `fathom info` output).                                     |
| `module_trace`  | list (opt.) | Ordered list of `{module, rule, fired_at}` entries showing which rules fired in what order.       |

The reason string is in-band; in earlier versions only an `input_hash` was
included. The current envelope includes both `decision` and `reason` so the
token alone proves *what* was decided and *why* (per the firing rule's
declared reason). Pair with the audit log for the full input fact set.

## Public-key distribution

Fathom releases publish the verifying public key in two places:

- As a base64-encoded PEM file at `<release-url>/fathom-pubkey.pem` (the
  release URL is the GitHub release page for the matching engine version).
- Inline in the GitHub release notes for that version.

Key fingerprint: take the DER-encoded SubjectPublicKeyInfo, sha256 it, hex
encode, and use the first 16 hex characters as the fingerprint. Operators
should pin the fingerprint at deploy time so a key rotation is an explicit,
visible event.

## Verify pseudocode

Working snippet using `cryptography` and `PyJWT`:

```python
import base64
import hashlib
import jwt  # PyJWT
from cryptography.hazmat.primitives import serialization

PEM = open("fathom-pubkey.pem", "rb").read()
public_key = serialization.load_pem_public_key(PEM)

# Pin the fingerprint at deploy time.
EXPECTED_FP = "9c1b2a3d4e5f6071"

der = public_key.public_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)
fp = hashlib.sha256(der).hexdigest()[:16]
assert fp == EXPECTED_FP, f"unexpected pubkey fingerprint: {fp}"

def verify(token: str, *, expected_iss: str = "fathom") -> dict:
    payload = jwt.decode(
        token,
        public_key,
        algorithms=["EdDSA"],
        options={"require": ["iss", "sub", "iat", "exp", "decision"]},
        issuer=expected_iss,
    )
    # Optional: pin engine_version and ruleset_hash.
    return payload

# Example usage
token = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9..."
claims = verify(token)
print(claims["decision"], claims["reason"])
```

`jwt.decode` raises on:

- bad signature,
- malformed token,
- wrong `alg`,
- `exp` in the past,
- missing required claim,
- `iss` mismatch.

Catch `jwt.PyJWTError` (or, in Fathom's own code, `AttestationError`) at the
boundary.

## Threat model

What attestation **does** protect against:

- Disputes about what was decided. The signed `decision` and `module_trace`
  pin the answer to the rules that produced it.
- Tampering with exported logs. An attacker who modifies the JWT can't
  re-sign without the private key; verification fails.

What it **does not** protect against:

- A compromised engine. If the process producing tokens is controlled by an
  attacker, it simply signs whatever it wants. Fathom cannot attest to its
  own integrity — that is the loader's job.
- Private-key theft. Custody of the signing key is out of scope.
- Side channels. Timing, cache behaviour, and downstream effects can still
  leak decisions.

## See also

- `rule-yaml-schema.md` — `attestation: true` field on a rule's `then` block
  is metadata; signing is enabled at engine construction.
- `rule-packs.md` — packs that ship attestation-flagged rules.
