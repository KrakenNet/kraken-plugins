# Nautilus Plugin

Slash commands and agents for authoring + operating Nautilus brokers.

## Commands

| Command | Purpose |
|---|---|
| `/nautilus:new-source` | Append a source block to nautilus.yaml |
| `/nautilus:new-adapter <name>` | Scaffold an adapter package |
| `/nautilus:new-rule-pack <name>` | New routing rule pack |
| `/nautilus:request` | POST /v1/request |
| `/nautilus:sources` | GET /v1/sources + enable/disable |
| `/nautilus:caps` | Show + edit cost caps |
| `/nautilus:adapter-coverage <adapter>` | SN-style coverage matrix |
| `/nautilus:audit-tail` | Tail JSONL audit log |
| `/nautilus:verify-attestation <token>` | Verify JWS |
| `/nautilus:nautobot-test` | Connection test for Nautobot adapter |

## Agents

- `source-builder`
- `adapter-builder`
- `broker-driver`
- `attestation-verifier`

## Skills

- `smart-nautilus`
- `smart-kraken`

## Install

```bash
claude plugins marketplace add ./kraken-plugins
claude plugins install nautilus
```
