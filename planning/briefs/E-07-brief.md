# Worker Brief — E-07: Hero-Path Integration

- **Work-Item ID:** `E-07`
- **Assigned Worker Model:** `gemini-3.8-flash`, thinking level `medium`
- **Coordinator:** `gemini-3.8-flash`, thinking level `high`
- **Branch:** `gemini/E-07-hero-path-integration`
- **Dependencies & Input Commits:** Depends on `E-03`, `E-04`, `E-05`, `E-06` (commit `282006b`)

---

## 1. Outcome

A complete, production-ready, vertical slice connecting the Next.js API route handlers (BFF) to the domain recommendation engine, safety policy verifier, and storage adapter, fully validated by end-to-end integration tests executing the complete Golden Path demo arc.

---

## 2. Owned Files & Excluded Files

### Owned Files
- `src/app/api/fleet/route.ts`
- `src/app/api/assets/[id]/route.ts`
- `src/app/api/work-orders/route.ts`
- `src/app/api/audit/route.ts`
- `src/app/api/admin/reset/route.ts`
- `tests/e2e-hero-path.test.ts`
- `planning/briefs/E-07-brief.md`

### Excluded Files
- Core domain entity definitions (Owned by `E-02`)
- UI Components (Owned by `E-05`)

---

## 3. Exact Requirements & Non-Goals

### Exact Requirements
1. **API Route Handlers (`src/app/api/`):**
   - `GET /api/fleet`: Returns list of all equipment assets with status and latest telemetry summary.
   - `GET /api/assets/[id]`: Returns asset entity, active diagnostic faults, full telemetry history, and dynamically evaluated `Recommendation`.
   - `POST /api/work-orders`: Validates payload via `SafetyPolicyVerifier`. Rejects unconfirmed orders (`400 Bad Request`). Inserts order and creates audit event with SHA-256 hash. Returns `201 Created`.
   - `GET /api/work-orders`: Returns dispatched orders list.
   - `GET /api/audit`: Returns compliance audit events list.
   - `POST /api/admin/reset`: Restores `globalStorage` in-memory state to pristine seed fixtures. Returns `200 OK`.
2. **End-to-End Integration Suite (`tests/e2e-hero-path.test.ts`):**
   - Executes complete 6-stage Hero Arc:
     1. Fleet Ingestion & Health Scan.
     2. Anomaly Detection on Asset 336 (overheating 108.5°C + SPN 110).
     3. Advisory Recommendation Generation with citations.
     4. Safety Gate enforcement (unauthorized dispatch rejected).
     5. Human Confirmation & Work Order Dispatch.
     6. Immutable Audit Event Verification & Demo Reset.

### Non-Goals
- Do not add complex external auth tokens (use demo persona header).
- Do not introduce microservice proxying.

---

## 4. Acceptance Criteria

- All route handlers return valid JSON responses with appropriate HTTP status codes (200, 201, 400, 404).
- End-to-end integration tests verify the complete Hero Golden Path without failures.
- `npm run test` passes with 100% tests green.
