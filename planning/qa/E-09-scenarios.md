# QA Scenarios — E-09: Demo, Evidence, and Presentation Integration

- **Work-Item ID:** `E-09`
- **Assigned QA Designer Model:** `gemini-3.8-flash`, thinking level `medium`
- **Date:** 2026-09-22

---

## Scenario Catalog

### Scenario QA-E09-01: Demo Golden Path Completeness
- **Scenario ID:** `QA-E09-01`
- **Requirement/Work-Item ID:** `E-09-REQ-01`
- **Preconditions:** `demo-script.md` drafted.
- **Exact Actions or Commands:**
  Verify that the demo script specifies minute-by-minute cues, actor dialog, button click sequences, and emergency reset instructions.
- **Expected Result:** Script matches the Golden Demo Path in Manifest Section 2.
- **Concrete Pass Criteria:** All 8 golden path steps documented with timing budgets.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E09-02: Fallback Coverage Across Failure Modes
- **Scenario ID:** `QA-E09-02`
- **Requirement/Work-Item ID:** `E-09-REQ-02`
- **Preconditions:** `fallback-matrix.md` drafted.
- **Exact Actions or Commands:**
  Inspect contingency matrix for coverage of network drop, UI freeze, corrupt state, and judge Q&A drill.
- **Expected Result:** Clear fallback protocol for each critical eventuality.
- **Concrete Pass Criteria:** 100% critical failure modes covered.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E09-03: Claims Ledger Traceability
- **Scenario ID:** `QA-E09-03`
- **Requirement/Work-Item ID:** `E-09-REQ-03`
- **Preconditions:** `evidence-register.md` drafted.
- **Exact Actions or Commands:**
  Cross-reference each declared claim (e.g., "100% deterministic replay", "sub-100ms API evaluation", "tamper-evident audit") with corresponding Vitest test cases.
- **Expected Result:** Zero unevidenced marketing claims.
- **Concrete Pass Criteria:** Every claim links to an active test file and scenario ID.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION
