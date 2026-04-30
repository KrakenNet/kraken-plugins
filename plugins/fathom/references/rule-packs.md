# Rule Packs

Catalogue of rule packs that ship with Fathom or are planned. Each pack lives
under `src/fathom/rule_packs/<pack-name>/` in the source repo. Pack versions
pin to a specific spec revision; bump the pack's `version:` when the spec
changes.

## fathom-owasp-agentic

OWASP LLM Top 10 — agentic safety mitigations.

- **Pack version:** `1.0`
- **Rule count:** 4
- **Modules:** `owasp`
- **Templates:** `agent_input`, `agent_output`, `tool_call`
- **Decision space:** `escalate`, `deny`
- **Key facts:** prompt injection patterns in agent input; dangerous tool calls
  (LLM04 Excessive Agency); SSN / email leakage in agent output
  (LLM06 Insecure Output).
- **Source:** `src/fathom/rule_packs/owasp_agentic/`

## fathom-nist-800-53

NIST SP 800-53 — access control, audit, and information-flow controls.

- **Pack version:** `1.0`
- **Rule count:** 10
- **Modules:** `nist`
- **Templates:** `access_request`, `audit_event`, `data_transfer`
- **Decision space:** `allow`, `deny`, `escalate`
- **Key facts:** subject clearance vs. resource classification (AC-3, AC-4);
  cross-domain transfers; auditable events (AU-2, AU-3).
- **Source:** `src/fathom/rule_packs/nist_800_53/`

## fathom-hipaa

HIPAA Privacy and Security Rule — PHI handling, minimum necessary, breach.

- **Pack version:** `1.0`
- **Rule count:** 3
- **Modules:** `hipaa`
- **Templates:** `phi_policy`, `data_transfer`
- **Decision space:** `allow`, `deny`, `escalate`
- **Key facts:** PHI data class, transfer purpose (treatment / payment /
  operations), minimum-necessary scope, breach-trigger thresholds (>500
  affected individuals → notification escalation).
- **Source:** `src/fathom/rule_packs/hipaa/`

## fathom-cmmc

CMMC Level 2+ — Controlled Unclassified Information (CUI) controls.

- **Pack version:** `1.0`
- **Rule count:** 6
- **Modules:** `cmmc`
- **Templates:** `cui_policy`
- **Decision space:** `allow`, `deny`, `escalate`
- **Key facts:** CUI category, marking, system enclave boundary, access
  authorization. Maps to AC, AU, IA, SC families at Level 2.
- **Source:** `src/fathom/rule_packs/cmmc/`

## fathom-ssvc

CISA Stakeholder-Specific Vulnerability Categorization v2.0.3 — coordinator
triage decision tree.

- **Pack version:** `2.0.3` (pins exactly to the CISA spec rev).
- **Rule count:** 17 (one per branch of the v2.0.3 decision tree).
- **Modules:** `ssvc`
- **Templates:** `exploitation`, `exposure`, `automatable`, `mission_impact`,
  `ssvc_meta`
- **Decision space (outputs):** `Act`, `Attend`, `Track*`, `Track`
- **Inputs:** Exploitation (`none|poc|active`), Exposure
  (`small|controlled|open`), Automatable (`yes|no`), MissionImpact
  (`degraded|mef_support_crippled|mef_failure|mission_failure`)
- **Version-pin policy:** the pack's `version:` MUST equal the CISA spec rev.
  When CISA publishes a new SSVC revision, ship a new pack version side-by-side
  rather than mutating the existing one — operators relying on a specific
  decision tree need a stable artifact.
- **Spec source:** https://www.cisa.gov/ssvc and the CMU/SEI SSVC paper.
- **Source:** `src/fathom/rule_packs/ssvc/`

## Authoring a new pack

Use `/fathom:new-rule-pack <pack-name>`. The `rule-pack-builder` agent
scaffolds `pack.yaml`, `templates/`, `rules/`, `modules/`, `functions/`,
`tests/`, and a starter `README.md`, then runs `fathom validate` and
`pytest tests/` in a build-test-fix loop.

Conventional layout:

```
<pack-name>/
  pack.yaml
  README.md
  templates/
  rules/
  modules/
  functions/
  tests/
```

## See also

- `rule-yaml-schema.md` — schema for files inside `templates/`, `rules/`,
  `modules/`, `functions/`.
- `clips-cheatsheet.md` — operators usable in rule conditions.
