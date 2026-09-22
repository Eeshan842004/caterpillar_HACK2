# QA Scenarios — E-03: Ingestion and Storage Profile

- **Work-Item ID:** `E-03`
- **Assigned QA Designer Model:** `gemini-3.8-flash`, thinking level `medium`
- **Date:** 2026-09-22

---

## Scenario Catalog

### Scenario QA-E03-01: Ingestion Quality Tagging (Physical Boundary Exceeded)
- **Scenario ID:** `QA-E03-01`
- **Requirement/Work-Item ID:** `E-03-REQ-01`
- **Preconditions:** IngestionService initialized.
- **Fixture & Seed Version:** N/A
- **Exact Actions or Commands:**
  Submit a telemetry measurement with coolant temperature = 195°C (exceeding 150°C physical max).
- **Expected Result:** Measurement is ingested but tagged with `quality: 'OUT_OF_RANGE'`.
- **Concrete Pass Criteria:** `point.quality === 'OUT_OF_RANGE'`.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E03-02: Stale Telemetry Detection
- **Scenario ID:** `QA-E03-02`
- **Requirement/Work-Item ID:** `E-03-REQ-02`
- **Preconditions:** IngestionService initialized.
- **Exact Actions or Commands:**
  Submit a telemetry measurement observed 6 hours in the past.
- **Expected Result:** Measurement is tagged with `quality: 'STALE'`.
- **Concrete Pass Criteria:** `point.quality === 'STALE'`.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E03-03: Repository CRUD and Query Isolation
- **Scenario ID:** `QA-E03-03`
- **Requirement/Work-Item ID:** `E-03-REQ-03`
- **Preconditions:** In-memory repository loaded.
- **Exact Actions or Commands:**
  Create a new work order for asset `ast_336_001`. Query `findAll()` and `findById()`.
- **Expected Result:** Work order is retrieved with exact assigned properties.
- **Concrete Pass Criteria:** Retrieved order matches created order.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E03-04: Deterministic Repository Reset
- **Scenario ID:** `QA-E03-04`
- **Requirement/Work-Item ID:** `E-03-REQ-04`
- **Preconditions:** Repository populated, mutated with added work order and status changes.
- **Exact Actions or Commands:**
  Call `storage.reset()`.
- **Expected Result:** Work orders array emptied, assets restored to initial seed counts and statuses.
- **Concrete Pass Criteria:** All entities match pristine seed fixtures.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION
