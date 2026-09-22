# QA Execution Evidence & Scoreboard — E-02: Domain Contracts and Deterministic Fixtures

- **Work-Item ID:** `E-02`
- **Execution Date:** 2026-09-22
- **Scoreboard:** **5 PASSED / 0 FAILED / 0 BLOCKED**

---

## Execution Results

| Scenario ID | Name | Command Executed | Result | Status |
|---|---|---|---|:---:|
| `QA-E02-01` | Identifier Separation Invariant | `npx vitest run tests/domain.test.ts` | All assets have distinct `id` and `serial_number` | **PASS** |
| `QA-E02-02` | Dual Timestamp & UTC Policy | `npx vitest run tests/domain.test.ts` | Valid ISO 8601 UTC strings, `ingested_at >= observed_at` | **PASS** |
| `QA-E02-03` | Data Quality Enum Validation | `npx vitest run tests/domain.test.ts` | Stale point on `ast_745_002` verified, valid enum states | **PASS** |
| `QA-E02-04` | Ground Truth Anomaly Verification | `npx vitest run tests/domain.test.ts` | `ast_336_001` reaches 108.5°C (>102°C threshold) + SPN 110 FMI 0 | **PASS** |
| `QA-E02-05` | Fixture Deep-Clone & Replay | `npx vitest run tests/domain.test.ts` | Deep clone verified; mutation doesn't taint fresh reload | **PASS** |

---

## Vitest Command Output
```text
 ✓ tests/domain.test.ts (6 tests) 6ms
 Test Files  1 passed (1)
      Tests  6 passed (6)
```
