# Nautilus Audit JSONL

The Nautilus broker writes one JSON object per line to its audit sink for every request it handles. The default sink is a file (`./audit.jsonl`), configured under `audit:` in `nautilus.yaml`.

## Entry Shape

Each line is a single self-contained JSON object:

| Field | Type | Description |
|---|---|---|
| `request_id` | string (UUID) | Unique request identifier. Matches `request_id` in the attestation payload. |
| `agent_id` | string | Caller identity. |
| `intent` | string | Caller-supplied intent. |
| `outcome` | string | `success`, `denied`, or `error`. |
| `sources_queried` | list[string] | Source IDs the broker actually queried. |
| `sources_denied` | list[string] | Source IDs the broker refused. |
| `attestation_token` | string | Full JWS string (base64url segments separated by `.`). Empty for `error` outcomes. |
| `error` | string | Error message. Present only when `outcome == "error"`. |
| `timestamp` | string (RFC3339) | UTC timestamp the request completed. |
| `duration_ms` | int | Wall-clock duration in milliseconds. |

Example line (formatted for readability — actual file is single-line per entry):

```json
{
  "request_id": "8b1f6a2e-...-4c",
  "agent_id": "incident-triage",
  "intent": "summarize ticket INC0012345",
  "outcome": "success",
  "sources_queried": ["incidents", "kb-vectors"],
  "sources_denied": ["prod-customer-pg"],
  "attestation_token": "eyJhbGciOi...",
  "timestamp": "2026-04-30T12:34:56Z",
  "duration_ms": 412
}
```

## Append-Only + fsync

The broker opens the audit file in append mode (`open(path, "a")`) and, when `audit.fsync: true` (the default), calls `os.fsync()` after each line write.

This guarantees:

- No interleaving between concurrent writers (single-process append is atomic for small writes on POSIX).
- Each line is durable to disk before the broker returns the response to the caller.

The cost is one fsync per request. For high-throughput deployments operators may set `audit.fsync: false` and accept the durability tradeoff, or front the file with a streaming sink (Kafka, etc.).

## Common Queries

Recent denials:

```bash
tail -100 audit.jsonl | jq 'select(.outcome=="denied")'
```

Per-source heatmap (count requests by queried source):

```bash
jq -r '.sources_queried[]' audit.jsonl | sort | uniq -c | sort -rn
```

Top denying sources:

```bash
jq -r '.sources_denied[]' audit.jsonl | sort | uniq -c | sort -rn
```

Lookup by request_id:

```bash
grep '"<request_id>"' audit.jsonl | jq
```

Errors in the last hour (RFC3339 lexicographic compare works):

```bash
NOW=$(date -u -Iseconds)
HOUR_AGO=$(date -u -d '1 hour ago' -Iseconds)
jq -c "select(.outcome==\"error\" and .timestamp >= \"$HOUR_AGO\")" audit.jsonl
```

P95 duration for an agent:

```bash
jq -r 'select(.agent_id=="incident-triage") | .duration_ms' audit.jsonl \
  | sort -n | awk 'BEGIN{c=0} {a[c++]=$1} END{print a[int(c*0.95)]}'
```

## Rotation

The broker does NOT rotate the audit log. Rotation is the operator's responsibility. Recommended approaches:

- **logrotate** (Linux): `copytruncate` to avoid disrupting the broker's open file handle, with `dateext` and a retention window matching your compliance policy.
- **Streaming sink** (replaces the JSONL file entirely): mount the audit path on a named pipe or tail-and-ship via Vector/Fluent Bit to Kafka, S3, or an SIEM.
- **Manual cron**: nightly `mv audit.jsonl audit-$(date -I).jsonl && touch audit.jsonl`. Note: the broker's append handle will continue writing to the original inode unless restarted; prefer `copytruncate`.

When rotating, do NOT re-order or merge lines across files — the order of entries within a file is the broker's append order and is what verification tools rely on.
