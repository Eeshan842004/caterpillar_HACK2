# Industrial Asset Operations Workspace

> **A trustworthy, advisory decision-support workspace for heavy equipment fleet managers to triage telematics faults, inspect thermal anomalies, and authorize verified maintenance dispatches.**

---

## 1. Executive Summary

- **Current Status:** **DEMO-READY / SUBMITTED** (Council Review Verdict SHA `c00bdca0` | Release Tag `v1.0.0-hackathon-final`)
- **Primary User:** **Alex Vance**, Field Service Supervisor managing distributed heavy machinery across remote quarry and construction sites.
- **The Core Problem:** Heavy equipment fleets generate thousands of raw telematics alerts daily. Alert fatigue obscures critical early warnings—leading either to catastrophic engine failure ($50,000+ per machine) or expensive false technician dispatches.
- **The Solution:** A modular industrial decision spine that turns raw ISO 15143-3 sensor streams and J1939 fault codes into evidence-backed, human-verified maintenance work orders in under 2 minutes.

---

## 2. Key Features

- **Fleet Health Workspace:** Live fleet overview displaying operating status (`CRITICAL`, `WARNING`, `NOMINAL`), engine hours, and fuel levels across connected equipment units.
- **Thermal Trajectory Visualizer:** Recharts timeline charting engine coolant temperature spikes against calibrated warning (102°C) and critical (106°C) thresholds.
- **Deterministic Diagnostic Engine:** Rule-based diagnostic evaluator correlating active Diagnostic Trouble Codes (`SPN 110 FMI 0`) with sensor trends to generate confidence-scored advisory recommendations.
- **Safety Compliance Gate (ADR-0003):** Strictly advisory decision support. Zero direct or autonomous machinery actuation. All consequential work orders require explicit human authorization.
- **Offline Field Resilience:** Client-side draft queue with unique idempotency keys that prevents duplicate work orders when synchronizing after connectivity loss.
- **Tamper-Evident Audit Trail:** Every consequential authorization event is sealed with a SHA-256 cryptographic hash for compliance verification.
- **Sub-150ms Instant Reset:** One-click demo state reset to pristine ground truth seed fixtures for 100% deterministic presentation replays.

---

## 3. Architecture Snapshot

```text
[ Connected Equipment Fleet ]
  │ (ISO 15143-3 Telematics & J1939 Faults)
  ▼
[ 1. Ingestion & Quality Validation ] ──► (Detects STALE, OUT_OF_RANGE, GOOD)
  │
  ▼
[ 2. Recommendation Engine ] ──────────► (Evaluates rules, calculates confidence, bundles citations)
  │
  ▼
[ 3. Safety Compliance Gate ] ─────────► (Enforces ADR-0003: Mandatory Human Approver Signature)
  │
  ▼
[ 4. Operational Workspace UI ] ───────► (Next.js 14 App Router, Recharts, Dark Industrial Theme)
  │
  ▼
[ 5. Persistence & Audit Ports ] ──────► (Storage-neutral in-memory baseline + SHA-256 Audit Trail)
```

---

## 4. Setup & Local Run Instructions

### Prerequisites
- Node.js `>= 20.10.0 LTS`
- npm `>= 10.2.0`

### Quick Start
```powershell
# 1. Clone & Enter Directory
cd c:\Users\kriss\github\caterpillar-hack\caterpillar-hack

# 2. Install Dependencies
npm install

# 3. Start Development Server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to view the operational workspace.

### Automated Verification Commands
```powershell
# Run all 36 automated unit, contract, and E2E integration tests
npm run test

# Run strict TypeScript type check
npm run type-check

# Run Next.js ESLint check
npm run lint

# Build production bundle
npm run build
```

---

## 5. Live Judging Demo (Golden Path)

1. **Fleet Overview:** Open `http://localhost:3000`. Observe 4 connected machines and the amber "SYNTHETIC DEMO DATA" compliance header.
2. **Select Hero Asset:** Click on **CAT-336-HEX-8821** (marked `CRITICAL`).
3. **Inspect Anomaly:** Observe the coolant temperature curve spiking from 92°C to 108.5°C, breaching the 102°C threshold, accompanied by active fault `SPN 110 FMI 0`.
4. **Review Recommendation:** Examine the 94% confidence emergency advisory with cited sensor evidence.
5. **Human Safety Gate:** Click **"Review & Confirm Work Order →"**. In the modal, verify technician assignment, enter authorization notes, and click **"Authorize & Dispatch Work Order"**.
6. **Audit Verification:** Observe the dispatched work order and the new entry in the immutable Audit Trail.
7. **Offline Mode:** Click **"Simulate: Go Offline"** in the banner to demonstrate resilient local queueing.
8. **Instant Reset:** Click **"↺ Reset Demo State"** to restore pristine ground truth in 150ms.

---

## 6. Engineering Rigor & QA Scoreboard

| Metric | Measured Value |
|---|:---:|
| **Automated Tests** | **36 / 36 Passing (100%)** |
| **QA Scenario Scoreboard** | **34 / 34 Passed (0 Failed, 0 Blocked)** |
| **Type Check Diagnostics** | **0 Errors (`strict: true`)** |
| **ESLint Warnings/Errors** | **0 Warnings, 0 Errors** |
| **Average API Response Time** | **< 20 ms (In-Memory Baseline)** |
| **Deterministic Reset Time** | **< 150 ms** |

---

## 7. Repository Directory Map

```text
├── docs/
│   ├── diagrams/system-architecture.svg   # Vector architecture diagram
│   └── 10-presentation/                   # Presentation deck, script, fallback matrix
├── planning/
│   ├── challenge-compiler.md              # 1-page reveal-to-scope sheet
│   ├── implementation-manifest.md         # Pinned stack and product contract
│   ├── lock-trigger-register.md           # Lock/Trigger/Evidence register
│   ├── rules-and-provenance.md            # Competition governance & provenance
│   ├── decisions.md                       # Accepted ADRs (ADR-0001 to ADR-0005)
│   ├── briefs/                            # Multi-agent worker briefs (E-01 to E-10)
│   ├── qa/                                # QA scenario catalogs
│   ├── reviews/                           # High-reasoning adversarial reviews
│   └── evidence/                          # QA execution logs and final scoreboard
├── src/
│   ├── domain/                            # Storage-neutral entities, constants, services
│   ├── adapters/                          # In-memory repository container & fixtures
│   ├── components/                        # React UI workspace & Recharts visualizer
│   └── app/                               # Next.js App Router & API Route Handlers
├── tests/                                 # Vitest unit, contract, and E2E suites
├── CONTEXT.md                             # Live project truth and team roles
└── README.md                              # Entry point for judges and reviewers
```
