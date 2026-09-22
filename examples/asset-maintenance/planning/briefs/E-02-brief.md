# Worker Brief — E-02: Domain Contracts and Deterministic Fixtures

- **Work-Item ID:** `E-02`
- **Assigned Worker Model:** `gemini-3.8-flash`, thinking level `medium`
- **Coordinator:** `gemini-3.8-flash`, thinking level `high`
- **Branch:** `gemini/E-02-domain-contracts`
- **Dependencies & Input Commits:** Depends on `E-01` (commit `b19517b`)

---

## 1. Outcome

Storage-neutral domain entities, schemas, unit/time policies, deterministic fixture datasets, ground-truth scenarios, and fixture reset mechanisms that serve as the single source of truth for all downstream epics (E-03 through E-07).

---

## 2. Owned Files & Excluded Files

### Owned Files
- `src/domain/types.ts`
- `src/domain/constants.ts`
- `src/domain/fixtures/seed_assets.json`
- `src/domain/fixtures/seed_telemetry.json`
- `src/domain/fixtures/seed_faults.json`
- `src/domain/fixtures/loader.ts`
- `tests/domain.test.ts`
- `planning/briefs/E-02-brief.md`

### Excluded Files
- `src/adapters/` (Owned by `E-03`)
- `src/app/api/` (Owned by `E-03` / `E-07`)
- UI components and pages (Owned by `E-05`)

---

## 3. Exact Requirements & Non-Goals

### Exact Requirements
1. **Domain Types (`src/domain/types.ts`):**
   - Entities: `Asset`, `TelemetryPoint`, `DiagnosticFault`, `Recommendation`, `WorkOrder`, `AuditEvent`.
   - Distinguish internal IDs (`ast_...`) from external serials (`CAT-336-HEX-8821`).
   - Telemetry must feature dual timestamps (`observed_at` and `ingested_at` in UTC ISO 8601).
   - Data quality states enum: `GOOD`, `SUSPECT`, `STALE`, `MISSING`, `OUT_OF_RANGE`.
   - Audit events must record human actor, action, timestamp, target ID, and reason snapshot.
2. **Canonical Units (`src/domain/constants.ts`):**
   - Canonical metric units (`°C`, `kPa`, `L/h`, `km/h`, `hours`).
   - Normal operating threshold definitions per asset model.
3. **Deterministic Seed Fixtures:**
   - Seed version `seed_cat_2026_v1`.
   - Scenario 1 (Hero): Excavator `ast_336_001` showing escalating coolant temperature reaching 108°C and active fault `SPN 110 FMI 0`.
   - Scenario 2 (Degraded Sensor): Haul Truck `ast_745_002` with stale telemetry (`>12h` old).
   - Scenario 3 (Nominal Asset): Wheel Loader `ast_980_003` with all parameters in healthy ranges.
   - Scenario 4 (Maintenance Due): Track Loader `ast_963_004` approaching 2,000-hour major service interval.
4. **Fixture Loader (`src/domain/fixtures/loader.ts`):**
   - Pure function returning deep-cloned pristine copies of the seeded data.
   - Deterministic reset helper.

### Non-Goals
- Do not import database drivers or storage APIs.
- Do not make HTTP or network requests in domain models.

---

## 4. Acceptance Criteria

- All types export cleanly with strict TypeScript compilation.
- Fixture loader produces valid, deeply cloned domain objects.
- `tests/domain.test.ts` passes with 100% assertions covering entity validation, timestamps, thresholds, and fixture integrity.
