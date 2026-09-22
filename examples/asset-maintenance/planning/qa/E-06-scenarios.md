# QA Scenarios — E-06: Trust, Audit, and Offline Behavior

- **Work-Item ID:** `E-06`
- **Assigned QA Designer Model:** `gemini-3.8-flash`, thinking level `medium`
- **Date:** 2026-09-22

---

## Scenario Catalog

### Scenario QA-E06-01: Idempotent Offline Queue Synchronization
- **Scenario ID:** `QA-E06-01`
- **Requirement/Work-Item ID:** `E-06-REQ-01`
- **Preconditions:** OfflineSyncService loaded.
- **Fixture & Seed Version:** N/A
- **Exact Actions or Commands:**
  Queue a work order while offline. Call `syncAll()` twice in succession.
- **Expected Result:** Only one work order is created on storage; subsequent replay recognizes the `idempotency_key` and skips duplicate insertion.
- **Concrete Pass Criteria:** Exactly 1 work order recorded in repository.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E06-02: Tamper Detection on Audit Records
- **Scenario ID:** `QA-E06-02`
- **Requirement/Work-Item ID:** `E-06-REQ-02`
- **Preconditions:** Audit record with computed checksum.
- **Exact Actions or Commands:**
  Verify pristine audit record passes `verifyAuditRecord()`. Mutate payload property in memory and re-verify.
- **Expected Result:** Pristine returns `true`; mutated record returns `false` (tamper detected).
- **Concrete Pass Criteria:** Assertions pass.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E06-03: Safety Policy Rejection of Unconfirmed Action
- **Scenario ID:** `QA-E06-03`
- **Requirement/Work-Item ID:** `E-06-REQ-03`
- **Preconditions:** SafetyPolicyVerifier loaded.
- **Exact Actions or Commands:**
  Attempt to validate a work order payload where `approved_by` is missing or empty.
- **Expected Result:** Validation throws or returns `is_authorized: false`.
- **Concrete Pass Criteria:** Safety check blocks unauthorized dispatch.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E06-04: Offline UI State & Sync Indicator
- **Scenario ID:** `QA-E06-04`
- **Requirement/Work-Item ID:** `E-06-REQ-04`
- **Preconditions:** Workspace renders `OfflineSyncBanner`.
- **Exact Actions or Commands:**
  Toggle simulated connectivity state to "Offline". Queue an action. Verify pending badge displays "1 PENDING SYNC".
- **Expected Result:** UI reflects offline mode and pending item count.
- **Concrete Pass Criteria:** Assertions pass.
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION
