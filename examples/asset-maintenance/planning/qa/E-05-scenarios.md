# QA Scenarios — E-05: Operational Workspace

- **Work-Item ID:** `E-05`
- **Assigned QA Designer Model:** `gemini-3.8-flash`, thinking level `medium`
- **Date:** 2026-09-22

---

## Scenario Catalog

### Scenario QA-E05-01: Asset Fleet Selection & Status Rendering
- **Scenario ID:** `QA-E05-01`
- **Requirement/Work-Item ID:** `E-05-REQ-01`
- **Preconditions:** Workspace loaded.
- **Fixture & Seed Version:** `seed_cat_2026_v1`
- **Exact Actions or Commands:**
  Render `Workspace` component. Verify 4 equipment cards are visible, and asset `ast_336_001` renders with a red `CRITICAL` badge.
- **Expected Result:** All assets render with model names and status indicators.
- **Concrete Pass Criteria:** Assertions pass.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E05-02: Telemetry Chart & Evidence Rendering
- **Scenario ID:** `QA-E05-02`
- **Requirement/Work-Item ID:** `E-05-REQ-02`
- **Preconditions:** Hero asset `ast_336_001` selected.
- **Fixture & Seed Version:** `seed_cat_2026_v1`
- **Exact Actions or Commands:**
  Check telemetry chart container, active fault code badge `SPN 110 FMI 0`, and recommendation title.
- **Expected Result:** Displays overheating trajectory and citations.
- **Concrete Pass Criteria:** Assertions pass.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E05-03: Human-in-the-Loop Confirmation Modal Flow
- **Scenario ID:** `QA-E05-03`
- **Requirement/Work-Item ID:** `E-05-REQ-03`
- **Preconditions:** Recommendation card visible.
- **Exact Actions or Commands:**
  Click "Review & Confirm Work Order". Verify modal appears with dialog role. Click "Authorize & Dispatch Work Order".
- **Expected Result:** Modal closes, callback triggers work order creation, work order appears in Dispatched list.
- **Concrete Pass Criteria:** Order appears with status `DISPATCHED`.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E05-04: Reset Demo Determinism in UI
- **Scenario ID:** `QA-E05-04`
- **Requirement/Work-Item ID:** `E-05-REQ-04`
- **Preconditions:** Work order created.
- **Exact Actions or Commands:**
  Click "Reset Demo State" button.
- **Expected Result:** Work orders list returns to empty, asset state returns to pristine seed.
- **Concrete Pass Criteria:** Dispatched work orders cleared.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION
