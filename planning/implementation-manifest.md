# Implementation Manifest

> **Status:** Approved Baseline (Epic E-00 Freeze).  
> **Source:** [`GEMINI_MULTI_AGENT_IMPLEMENTATION_SPEC.md`](file:///c:/Users/kriss/github/caterpillar-hack/caterpillar-hack/GEMINI_MULTI_AGENT_IMPLEMENTATION_SPEC.md#L101-L198) Section 5.  
> **Governing Council Review:** Verdict SHA `c00bdca0`.

---

## 1. Identity

- **Challenge ID:** `CAT-HACK-REF-01`
- **Repository Root Confirmation:** Current Git repository root `c:\Users\kriss\github\caterpillar-hack\caterpillar-hack`. All paths are repository-relative.
- **Default Branch:** `main`
- **Event Start & Submission Deadline:** Kickoff 2026-09-22 00:00 IST | Submission 2026-09-22 23:59 IST (Timezone: `Asia/Calcutta`)
- **Team Roles & Availability:** 100% active full-stack & AI capability.
- **Coordinator Model & Level:** `gemini-3.8-flash`, thinking level `high`
- **Implementation Worker Model & Level:** `gemini-3.8-flash`, thinking level `medium`
- **QA & Scenario Worker Model & Level:** `gemini-3.8-flash`, thinking level `medium`
- **Review Worker Model & Level:** `gemini-3.8-flash`, thinking level `high`

---

## 2. Product

- **Primary User:** Maintenance Supervisor / Field Service Lead
- **Hero Behavior:** **Evidence-Based Fault Triage to Verified Work Order**  
  Ingest telemetry stream & diagnostic fault -> validate sensor data quality & freshness -> contextualize asset history -> evaluate rule-based severity -> generate evidence-backed maintenance recommendation with sensor citations -> require human supervisor review & confirmation -> dispatch work order and record immutable audit event.
- **Supporting Behaviors:**
  1. *Fleet Health Workspace:* Interactive asset telemetry charts with sensor quality and freshness badges.
  2. *Offline Field Queue:* Resilient local drafting of work orders with sync status indicator.
- **Golden Demo Path:**
  1. Open Operations Workspace; observe 4 connected equipment assets with live telemetry status.
  2. Select asset `ast_336_001` (Excavator 336-HEX-8821) showing escalating engine coolant temperature and active Diagnostic Trouble Code `SPN 110 FMI 0`.
  3. Inspect telemetry trend chart showing temperature spike to 108°C against warning threshold of 102°C.
  4. Review system-generated advisory recommendation: *"Emergency Service: Inspect Coolant Line and Radiator Core"*.
  5. Inspect cited sensor evidence, timestamps, and confidence score (94%).
  6. Click "Confirm & Dispatch Work Order" to trigger human-in-the-loop review modal.
  7. Confirm action -> observe work order dispatched and new entry in tamper-evident Audit Log.
  8. Trigger "Reset State" to verify deterministic replay.
- **Measurable Acceptance Outcomes:**
  - 100% reproducible demo and test replay from clean fixtures.
  - Zero ungrounded or uncited diagnostic claims.
  - Sub-100ms API response time for all local evaluations.
  - Full keyboard accessibility and responsive layout across desktop and tablet viewports.
- **Non-Goals:**
  - Direct or simulated control of physical machinery (no engine kill commands, no CAN bus transmission).
  - Universal J1939 fault code severity catalog across third-party OEMs.
  - Complex multi-tenant cloud authentication during demo.
- **Cut Order:**
  1. ElevenLabs voice narration.
  2. Complex offline conflict resolution (fall back to online draft mode).
  3. Advanced predictive statistical models (rely on deterministic heuristic rule engine).

---

## 3. Stack

- **Operating Systems Supported:** Windows 10/11, POSIX (Linux, macOS)
- **Runtime & Exact Version:** Node.js `>= 20.10.0 LTS`
- **Package Manager & Exact Version:** npm `>= 10.2.0`
- **Web/App Framework & Version:** Next.js `14.2.x` (App Router) + React `18.3.x` + TypeScript `5.4.x`
- **Styling:** Vanilla CSS & CSS Modules with CSS custom properties design tokens (charcoal, slate, steel, industrial amber/emerald/crimson)
- **Repository Layout:** Modular Monolith
  ```text
  src/
  ├── domain/          # Pure entities, schemas, business logic, ports
  ├── adapters/        # In-memory storage, mock data feeds, repositories
  ├── app/             # Next.js App Router pages and Route Handlers (BFF)
  └── components/      # UI workspace components, charts, modals
  ```
- **Server / BFF Choice:** Next.js Route Handlers (`src/app/api/*`)
- **Optional Python Service:** `disabled`
- **Persistence Profile:** Storage-neutral repository interfaces backed by deterministic local in-memory/JSON fixtures. (Hosted Supabase/Postgres adapter prepared but disabled).
- **Hosted Services Activated:** None
- **Chart Library:** `Recharts` (single approved charting library)
- **Test Runner & Tools:** `Vitest` (unit/integration tests), `@testing-library/react`
- **Code Quality Tools:** `ESLint`, `Prettier`, `tsc --noEmit`
- **Local Run & Test Commands:**
  - Dev server: `npm run dev`
  - Unit & contract tests: `npm run test`
  - Typecheck: `npm run type-check`
  - Lint: `npm run lint`
  - Build validation: `npm run build`

---

## 4. Data Policy

- **Identifier Mapping:**
  - Internal Asset ID: Stable prefixed UUIDv4 (e.g. `ast_336_001`). External Asset Serial: Distinct human-readable string (e.g. `CAT-336-HEX-8821`).
  - Internal Fault Event ID: Prefixed UUIDv4 (e.g. `flt_092a_4410`).
  - Work Order ID: Prefixed UUIDv4 (e.g. `wo_20260922_01`).
- **Canonical Units:** SI / Metric standard (`°C` for temperature, `kPa` for pressure, `L/h` for fuel flow, `h` for engine operating hours, `km/h` for speed).
- **Timestamp Policy:** ISO 8601 UTC strings (`YYYY-MM-DDTHH:mm:ss.sssZ`) for all internal records. UI renders with explicit site timezone (`Asia/Calcutta`).
- **Dual Timestamps:** Every telemetry event records both `observed_at` (sensor clock) and `ingested_at` (system receipt time).
- **Data Quality States:** Explicit enum on every measurement: `GOOD`, `SUSPECT`, `STALE`, `MISSING`, `OUT_OF_RANGE`.
- **Raw-Input Retention:** Ingested payloads preserve original unparsed JSON in `raw_input` attribute.
- **Synthetic Data & Ground Truth:**
  - Seed version: `seed_cat_2026_v1`
  - Scenario 1 (Ground Truth Hero): Asset `ast_336_001` with escalating coolant temp exceeding 102°C threshold + SPN 110 FMI 0 fault.
  - Scenario 2 (Degraded Sensor): Asset `ast_745_002` with stale telemetry (`>12 hours old`), degrading recommendation to "Insufficient Data / Schedule Physical Sensor Inspection".
  - Scenario 3 (Nominal Fleet Asset): Asset `ast_980_003` operating within all normal operating thresholds.
- **Reset Mechanism:** `POST /api/admin/reset` restores in-memory repository to pristine seed state.

---

## 5. Activated Capabilities Status

| Capability | Status | Fallback / Baseline Behavior | Owner |
|---|---|---|---|
| **Real Authentication** | `disabled` | Deterministic demo persona ("Alex Vance - Field Service Supervisor") | Lead Architect |
| **Supabase / Postgres** | `disabled` | Local in-memory repository implementing `StoragePort` | Data Lead |
| **MongoDB / Time-Series** | `disabled` | Structured JSON telemetry event array in memory | Data Lead |
| **Python / FastAPI** | `disabled` | Pure TypeScript deterministic rule evaluator | Analytics Lead |
| **Product LLM / RAG** | `disabled` | Deterministic rule engine with citation generator | AI Lead |
| **ElevenLabs Voice** | `disabled` | Full touch/keyboard accessible UI | UX Lead |
| **Mapping / GIS** | `disabled` | Structured site location cards | Frontend Lead |
| **Notifications / SMS** | `disabled` | In-app notification center | Backend Lead |
| **PDF Report Export** | `disabled` | Browser print media stylesheet | Frontend Lead |
| **Hosted Deployment** | `disabled` | Local dev server execution on `http://localhost:3000` | Dev Lead |

---

## 6. Safety & Compliance

- **Advisory Decision Support:** Strictly advisory. Software does not issue machine control or shutoff commands.
- **Human Confirmation:** Any consequential state change (work order dispatch, triage status change) requires an explicit human click and confirmation dialog.
- **Audit Event Logging:** All actions produce an immutable audit event recorded in `AuditRepository`.
- **Branding Compliance:** Neutral industrial styling ("Industrial Asset Operations"). No Caterpillar logos or protected trade dress.
- **Synthetic Data Label:** Clearly presented on all views as "SYNTHETIC DEMO DATA".

---

## 7. Delivery & Active Epics

### Active Epic List
- [x] **E-00:** Rules, manifest, and architecture freeze (COMPLETED)
- [ ] **E-01:** Repository foundation (scaffolding, runtime, quality tools)
- [ ] **E-02:** Domain contracts, schemas, and deterministic fixtures
- [ ] **E-03:** Ingestion and storage profile (storage-neutral repositories)
- [ ] **E-04:** Baseline analytics and recommendation engine
- [ ] **E-05:** Operational workspace (Next.js UI, charts, triage panel)
- [ ] **E-06:** Trust, audit, and offline safety controls
- [ ] **E-07:** Hero-path vertical slice integration & E2E verification
- [ ] **E-09:** Demo, evidence, and presentation integration
- [ ] **E-10:** Hardening, final tests, and submission package

*(Epics E-08A, E-08B, E-08C, E-08D are marked `disabled` per Section 5).*

### Dependency DAG
```text
E-00 (Freeze)
  └── E-01 (Foundation)
        └── E-02 (Domain Contracts & Fixtures)
              ├── E-03 (Storage Profile)
              ├── E-04 (Analytics Engine)
              ├── E-05 (Operational Workspace)
              └── E-06 (Trust & Audit)
                    └── E-07 (Hero-Path Integration)
                          └── E-09 (Demo & Presentation)
                                └── E-10 (Hardening & Package)
```
