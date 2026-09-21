# Worker Brief — E-09: Demo, Evidence, and Presentation Integration

- **Work-Item ID:** `E-09`
- **Assigned Worker Model:** `gemini-3.8-flash`, thinking level `medium`
- **Coordinator:** `gemini-3.8-flash`, thinking level `high`
- **Branch:** `gemini/E-09-presentation-integration`
- **Dependencies & Input Commits:** Depends on `E-07` (commit `e33125c`)

---

## 1. Outcome

A comprehensive presentation evidence pack, canonical architecture diagram source, step-by-step judge demo script with timing and fallbacks, and a verified claims ledger directly backed by automated test measurements.

---

## 2. Owned Files & Excluded Files

### Owned Files
- `docs/10-presentation/demo-script.md`
- `docs/10-presentation/fallback-matrix.md`
- `docs/10-presentation/evidence-register.md`
- `docs/10-presentation/story-arc.md`
- `docs/diagrams/system-architecture.svg`
- `planning/briefs/E-09-brief.md`

### Excluded Files
- Core application code (Owned by `E-01` through `E-07`)

---

## 3. Exact Requirements & Non-Goals

### Exact Requirements
1. **Demo Script (`docs/10-presentation/demo-script.md`):**
   - Minute-by-minute walkthrough (3–5 minute pitch & live demo).
   - Golden path covering Hero asset `ast_336_001` triage, temperature trajectory chart, SPN 110 active fault, advisory recommendation, human confirmation modal, and reset determinism.
2. **Fallback Matrix (`docs/10-presentation/fallback-matrix.md`):**
   - Explicit contingency plans for: network loss (offline mode), browser crash (deterministic seed reset), projection failure.
3. **Claims & Evidence Ledger (`docs/10-presentation/evidence-register.md`):**
   - Maps every judged claim to concrete automated tests, lines of code, and measured outputs.
4. **Architecture Diagram (`docs/diagrams/system-architecture.svg`):**
   - High quality SVG diagram illustrating the modular industrial spine: Ingestion -> Validation -> Recommendation Engine -> Safety Policy & Confirmation Gate -> In-Memory Persistence -> Audit Log.

---

## 4. Acceptance Criteria

- All documents exist and follow the specifications in `PRESENTATION_SYSTEM_PLAN.md`.
- Architecture diagram cleanly renders as standalone SVG.
- Claims register ties 100% of presentation claims to executable verification tests.
