# QA Scenarios — E-07: Hero-Path Integration

- **Work-Item ID:** `E-07`
- **Assigned QA Designer Model:** `gemini-3.8-flash`, thinking level `medium`
- **Date:** 2026-09-22

---

## Scenario Catalog

### Scenario QA-E07-01: Full Fleet Query via BFF API
- **Scenario ID:** `QA-E07-01`
- **Requirement/Work-Item ID:** `E-07-REQ-01`
- **Preconditions:** Server route handlers initialized.
- **Fixture & Seed Version:** `seed_cat_2026_v1`
- **Exact Actions or Commands:**
  Execute `GET /api/fleet`.
- **Expected Result:** HTTP 200, array of 4 assets with valid statuses, serials, and operating hours.
- **Concrete Pass Criteria:** Status 200, length === 4.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E07-02: Hero Asset Evaluation via BFF API
- **Scenario ID:** `QA-E07-02`
- **Requirement/Work-Item ID:** `E-07-REQ-02`
- **Preconditions:** Seed loaded.
- **Exact Actions or Commands:**
  Execute `GET /api/assets/ast_336_001`.
- **Expected Result:** HTTP 200, response contains asset, active faults including SPN 110 FMI 0, telemetry history, and an `IMMEDIATE` urgency recommendation with >90% confidence.
- **Concrete Pass Criteria:** Status 200, `recommendation.urgency === 'IMMEDIATE'`.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E07-03: Safety Policy Rejection of Anonymous Dispatch
- **Scenario ID:** `QA-E07-03`
- **Requirement/Work-Item ID:** `E-07-REQ-03`
- **Preconditions:** API running.
- **Exact Actions or Commands:**
  Execute `POST /api/work-orders` with empty `approved_by`.
- **Expected Result:** HTTP 400 Bad Request, response contains ADR-0003 safety violation message.
- **Concrete Pass Criteria:** Status 400, error message matches policy violation.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E07-04: Human Authorized Work Order Dispatch & Audit Trail
- **Scenario ID:** `QA-E07-04`
- **Requirement/Work-Item ID:** `E-07-REQ-04`
- **Preconditions:** API running.
- **Exact Actions or Commands:**
  Execute `POST /api/work-orders` with complete authorized payload.
- **Expected Result:** HTTP 201 Created, work order stored, new audit event recorded with valid SHA-256 hash.
- **Concrete Pass Criteria:** Status 201, audit event query includes new record.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E07-05: Reset State API Execution
- **Scenario ID:** `QA-E07-05`
- **Requirement/Work-Item ID:** `E-07-REQ-05`
- **Preconditions:** Work order dispatched.
- **Exact Actions or Commands:**
  Execute `POST /api/admin/reset`.
- **Expected Result:** HTTP 200 OK, `GET /api/work-orders` returns empty array, assets restored to initial seed.
- **Concrete Pass Criteria:** Status 200, work orders array length === 0.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION
