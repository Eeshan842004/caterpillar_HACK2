# Competition Rules and Pre-Event Provenance Register

> **Status:** Live active register (Epic E-00 baseline).  
> **Source:** [`PLANNING_A_TO_Z.md`](file:///c:/Users/kriss/github/caterpillar-hack/caterpillar-hack/PLANNING_A_TO_Z.md#L960-L970) Section 14.5 and [`GEMINI_MULTI_AGENT_IMPLEMENTATION_SPEC.md`](file:///c:/Users/kriss/github/caterpillar-hack/caterpillar-hack/GEMINI_MULTI_AGENT_IMPLEMENTATION_SPEC.md#L174-L186) Section 5.6.

---

## 1. Competition Governance & Rules

| Rule Area | Status / Ruling | Policy & Mitigation |
|---|---|---|
| **Pre-event Work** | Planning & Scaffolding Only | No application code, migrations, or live integrations existed prior to event kickoff. All application development occurs during the hackathon window. |
| **Third-Party & Open Source** | Permitted standard open-source | Standard MIT/Apache 2.0 open-source libraries permitted. All dependencies declared in lockfiles. |
| **AI Assistance** | Permitted with disclosure | Multi-agent AI tooling used for pair programming, test generation, and QA under human coordination. |
| **Intellectual Property** | Original work | Code created during the hackathon remains original work of the team. |
| **Branding & Trademark** | Restricted / No permission | Caterpillar trademarks, logos, trade dress, and official paint color hex codes are prohibited. Use neutral industrial theme ("Equipment Decision Support"). |
| **Safety & Control** | Decision Support Only | Strictly advisory. No direct or simulated autonomous machinery control. |

---

## 2. Pre-Event Provenance Ledger

This ledger explicitly tracks assets, specifications, and files created prior to the problem reveal to ensure strict competition integrity:

| Asset / File Path | Created Phase | Purpose & Content | Event-Created Derivation Rule |
|---|---|---|---|
| `PLANNING_A_TO_Z.md` | Pre-event | Governance, quality attributes, readiness gates | Non-binding guidance; superseded by ADRs |
| `GEMINI_MULTI_AGENT_IMPLEMENTATION_SPEC.md` | Pre-event | Architecture specification and epic contracts | Governs multi-agent coordinator handoff |
| `PRESENTATION_SYSTEM_PLAN.md` | Pre-event | Presentation evidence pipeline and slide structure | Template for final judging deliverables |
| `HACKATHON_STARTER_PACK_PLAN.md` | Pre-event | Non-binding capability reference catalog | Reference ideas only |
| `council-report-*` / `council-transcript-*` | Pre-event | Architecture council review (SHA `c00bdca0`) | Foundation for modular spine architecture |
| `planning/*.md` | Pre-event / Reveal | Active planning contracts and manifest | Live source of truth for implementation |
| `src/*` (to be created) | **Event-Created** | Application code, adapters, components, UI | 100% created during authorized hackathon window |
| `tests/*` (to be created) | **Event-Created** | Unit, contract, and integration tests | 100% created during authorized hackathon window |

---

## 3. Data Licensing & Synthetic Data Notice

- **Supplied Data:** If organizers supply datasets, they will be ingested strictly within stated license terms and preserved in an immutable raw format.
- **Synthetic Data Labeling:** All synthetic telematics, fault logs, fluid samples, and asset metadata are explicitly labeled as **"SYNTHETIC DATA — FOR DEMONSTRATION ONLY"** in:
  1. The application UI (header/banner and asset cards).
  2. Test fixtures and seed JSON files (`fixture_version` attribute).
  3. Presentation slides and demo scripts.

---

## 4. Industrial Safety & Confirmation Boundary

1. **Advisory Decision Support:** The software provides diagnostic insights, fault triage, and recommended work orders. It does **not** command engine start/stop, hydraulic actuation, speed limiting, or physical interlocks.
2. **Mandatory Human Confirmation:** Every consequential operational decision (e.g., dispatching field technician, deferring maintenance, altering operational load) requires an explicit click/confirmation by an authorized human operator.
3. **Audit Trail:** Every confirmation action produces an immutable audit record containing:
   - `action_id` (UUIDv4)
   - `timestamp` (UTC ISO 8601)
   - `user_persona` / `operator_id`
   - `action_type`
   - `target_asset_id`
   - `justification` & `evidence_snapshot`
