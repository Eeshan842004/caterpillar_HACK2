# QA Scenarios — E-04: Baseline Analytics and Recommendations

- **Work-Item ID:** `E-04`
- **Assigned QA Designer Model:** `gemini-3.8-flash`, thinking level `medium`
- **Date:** 2026-09-22

---

## Scenario Catalog

### Scenario QA-E04-01: Hero Overheating Anomaly Evaluation
- **Scenario ID:** `QA-E04-01`
- **Requirement/Work-Item ID:** `E-04-REQ-01`
- **Preconditions:** Asset `ast_336_001` with coolant temp 108.5°C and active SPN 110 FMI 0.
- **Fixture & Seed Version:** `seed_cat_2026_v1`
- **Exact Actions or Commands:**
  Evaluate asset using `RecommendationEngine.evaluate()`.
- **Expected Result:** Generates recommendation with `urgency: 'IMMEDIATE'`, `confidence_score >= 0.90`, citations including `engine_coolant_temp_c` = 108.5°C (> 102.0°C threshold).
- **Concrete Pass Criteria:** Assertions pass on urgency, citations, and suggested work order.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E04-02: Stale Telemetry Degradation
- **Scenario ID:** `QA-E04-02`
- **Requirement/Work-Item ID:** `E-04-REQ-02`
- **Preconditions:** Asset `ast_745_002` with `STALE` telemetry quality.
- **Fixture & Seed Version:** `seed_cat_2026_v1`
- **Exact Actions or Commands:**
  Evaluate asset using `RecommendationEngine.evaluate()`.
- **Expected Result:** Recommendation confidence drops below 0.50, title flags "Insufficient Evidence" or "Physical Inspection Required", prevents high-confidence automated dispatch.
- **Concrete Pass Criteria:** `confidence_score < 0.50` and rationale explicitly cites data staleness.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E04-03: Nominal Operating Asset Evaluation
- **Scenario ID:** `QA-E04-03`
- **Requirement/Work-Item ID:** `E-04-REQ-03`
- **Preconditions:** Asset `ast_980_003` with normal readings (86.5°C coolant) and zero active faults.
- **Fixture & Seed Version:** `seed_cat_2026_v1`
- **Exact Actions or Commands:**
  Evaluate asset using `RecommendationEngine.evaluate()`.
- **Expected Result:** Recommendation indicates `urgency: 'OBSERVE'`, no emergency work order required.
- **Concrete Pass Criteria:** `urgency === 'OBSERVE'`.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E04-04: Evidence Citation Traceability
- **Scenario ID:** `QA-E04-04`
- **Requirement/Work-Item ID:** `E-04-REQ-04`
- **Preconditions:** Any recommendation generated with citations.
- **Exact Actions or Commands:**
  Verify that all entries in `evidence_citations` contain non-null `parameter`, `observed_value`, `threshold_value`, `unit`, and ISO timestamp.
- **Expected Result:** Full provenance and citation completeness.
- **Concrete Pass Criteria:** Validation passes.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION
