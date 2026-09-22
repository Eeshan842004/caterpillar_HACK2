# QA Scenarios — E-01: Repository Foundation

- **Work-Item ID:** `E-01`
- **Assigned QA Designer Model:** `gemini-3.8-flash`, thinking level `medium`
- **Date:** 2026-09-22

---

## Scenario Catalog

### Scenario QA-E01-01: Clean Dependency Installation & Lockfile Consistency
- **Scenario ID:** `QA-E01-01`
- **Requirement/Work-Item ID:** `E-01-REQ-01`
- **Preconditions:** Node.js `>= 20.x` and npm `>= 10.x` installed. Clean working tree on `gemini/E-01-repo-foundation`.
- **Fixture & Seed Version:** N/A (Repository level)
- **Exact Actions or Commands:**
  ```powershell
  npm install
  ```
- **Expected Result:** Packages install without peer-dependency conflicts or critical audit vulnerabilities.
- **Concrete Pass Criteria:** Exit code `0`, `package-lock.json` generated.
- **Evidence Location:** `planning/evidence/E-01-qa.md`
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E01-02: Type Checker Strictness
- **Scenario ID:** `QA-E01-02`
- **Requirement/Work-Item ID:** `E-01-REQ-02`
- **Preconditions:** `npm install` succeeded, `tsconfig.json` has `strict: true`.
- **Fixture & Seed Version:** N/A
- **Exact Actions or Commands:**
  ```powershell
  npm run type-check
  ```
- **Expected Result:** TypeScript compiles across `src/` and `tests/` with 0 type errors.
- **Concrete Pass Criteria:** Exit code `0`, output contains no diagnostics.
- **Evidence Location:** `planning/evidence/E-01-qa.md`
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E01-03: Linter & Formatter Integrity
- **Scenario ID:** `QA-E01-03`
- **Requirement/Work-Item ID:** `E-01-REQ-03`
- **Preconditions:** Code created.
- **Exact Actions or Commands:**
  ```powershell
  npm run lint
  ```
- **Expected Result:** ESLint reports zero errors and zero warnings.
- **Concrete Pass Criteria:** Exit code `0`.
- **Evidence Location:** `planning/evidence/E-01-qa.md`
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E01-04: Test Harness Smoke Verification
- **Scenario ID:** `QA-E01-04`
- **Requirement/Work-Item ID:** `E-01-REQ-04`
- **Preconditions:** `vitest.config.ts` configured with JSDOM.
- **Exact Actions or Commands:**
  ```powershell
  npm run test
  ```
- **Expected Result:** Vitest discovers and executes `tests/foundation.test.ts` successfully.
- **Concrete Pass Criteria:** Exit code `0`, 100% tests passing.
- **Evidence Location:** `planning/evidence/E-01-qa.md`
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION

---

### Scenario QA-E01-05: Production Build Verification
- **Scenario ID:** `QA-E01-05`
- **Requirement/Work-Item ID:** `E-01-REQ-05`
- **Preconditions:** Next.js pages and config in place.
- **Exact Actions or Commands:**
  ```powershell
  npm run build
  ```
- **Expected Result:** Next.js production build succeeds, emitting `.next` build output.
- **Concrete Pass Criteria:** Exit code `0`, static routes compiled.
- **Evidence Location:** `planning/evidence/E-01-qa.md`
- **Owner:** QA Worker
- **Final Status:** PENDING EXECUTION
