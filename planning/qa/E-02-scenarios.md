# QA Scenarios — E-02: Domain Contracts and Deterministic Fixtures

- **Work-Item ID:** `E-02`
- **Assigned QA Designer Model:** `gemini-3.8-flash`, thinking level `medium`
- **Date:** 2026-09-22

---

## Scenario Catalog

### Scenario QA-E02-01: Identifier Separation Invariant
- **Scenario ID:** `QA-E02-01`
- **Requirement/Work-Item ID:** `E-02-REQ-01`
- **Preconditions:** `src/domain/types.ts` defined.
- **Fixture & Seed Version:** `seed_cat_2026_v1`
- **Exact Actions or Commands:**
  Run Vitest test checking that every asset fixture has a UUID-prefixed internal `id` (e.g., `ast_336_001`) that is distinct from its human-readable `serial_number` (e.g., `CAT-336-HEX-8821`).
- **Expected Result:** All assets strictly preserve internal vs external ID separation.
- **Concrete Pass Criteria:** Test passes.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E02-02: Dual Timestamp & UTC Policy
- **Scenario ID:** `QA-E02-02`
- **Requirement/Work-Item ID:** `E-02-REQ-02`
- **Preconditions:** Telemetry fixtures loaded.
- **Fixture & Seed Version:** `seed_cat_2026_v1`
- **Exact Actions or Commands:**
  Verify every telemetry record contains valid ISO 8601 UTC strings for both `observed_at` and `ingested_at`, and `ingested_at >= observed_at`.
- **Expected Result:** 100% of telemetry points adhere to dual timestamp invariant.
- **Concrete Pass Criteria:** Validation function passes without throwing.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E02-03: Data Quality Enum Validation
- **Scenario ID:** `QA-E02-03`
- **Requirement/Work-Item ID:** `E-02-REQ-03`
- **Preconditions:** Domain constants and types imported.
- **Exact Actions or Commands:**
  Verify telemetry quality values only take valid enum states (`GOOD`, `SUSPECT`, `STALE`, `MISSING`, `OUT_OF_RANGE`).
- **Expected Result:** All fixture records conform to the declared quality enum.
- **Concrete Pass Criteria:** Assertions pass.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E02-04: Ground Truth Anomaly Verification
- **Scenario ID:** `QA-E02-04`
- **Requirement/Work-Item ID:** `E-02-REQ-04`
- **Preconditions:** `seed_assets.json` and `seed_telemetry.json` loaded.
- **Fixture & Seed Version:** `seed_cat_2026_v1`
- **Exact Actions or Commands:**
  Inspect telemetry series for asset `ast_336_001`. Confirm temperature readings escalate beyond normal operating threshold (102°C) up to 108.5°C, matching active fault SPN 110 FMI 0.
- **Expected Result:** Ground truth anomaly present and matches Golden Path demo requirements.
- **Concrete Pass Criteria:** Assertions pass.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E02-05: Fixture Deep-Clone & Replay Determinism
- **Scenario ID:** `QA-E02-05`
- **Requirement/Work-Item ID:** `E-02-REQ-05`
- **Preconditions:** `loader.ts` fixture loader implemented.
- **Exact Actions or Commands:**
  Mutate loaded fixture object in memory, call `resetToDefaultSeed()`, and assert that the reloaded dataset is completely identical to pristine seed (immutability test).
- **Expected Result:** Deep-clone prevents in-memory mutation contamination across tests.
- **Concrete Pass Criteria:** Test passes.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION
