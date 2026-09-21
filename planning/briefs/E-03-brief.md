# Worker Brief — E-03: Ingestion and Storage Profile

- **Work-Item ID:** `E-03`
- **Assigned Worker Model:** `gemini-3.8-flash`, thinking level `medium`
- **Coordinator:** `gemini-3.8-flash`, thinking level `high`
- **Branch:** `gemini/E-03-storage-profile`
- **Dependencies & Input Commits:** Depends on `E-02` (commit `8a92dc7`)

---

## 1. Outcome

Storage-neutral repository ports and in-memory persistence adapters, alongside an ingestion validation service that classifies sensor data quality (`GOOD`, `OUT_OF_RANGE`, `STALE`) and preserves raw telemetry lineage.

---

## 2. Owned Files & Excluded Files

### Owned Files
- `src/domain/ports/repositories.ts`
- `src/domain/services/ingestion.ts`
- `src/adapters/in-memory-storage.ts`
- `tests/storage-ingestion.test.ts`
- `planning/briefs/E-03-brief.md`

### Excluded Files
- Analytics / recommendation logic (Owned by `E-04`)
- UI and Pages (Owned by `E-05`)
- Route Handlers API (Owned by `E-07`)

---

## 3. Exact Requirements & Non-Goals

### Exact Requirements
1. Define repository interfaces in `src/domain/ports/repositories.ts`:
   - `IAssetRepository`, `ITelemetryRepository`, `IFaultRepository`, `IWorkOrderRepository`, `IAuditRepository`.
2. Implement in-memory repository adapter in `src/adapters/in-memory-storage.ts`:
   - Pre-loaded from `E-02` seed data.
   - `reset()` method restores seed data completely.
   - CRUD operations for assets, faults, telemetry, work orders, audit events.
3. Implement `IngestionService` in `src/domain/services/ingestion.ts`:
   - Accepts raw or normalized sensor inputs.
   - Assigns `ingested_at` timestamp.
   - Detects `OUT_OF_RANGE` (e.g. coolant temp `< -40` or `> 150°C`, oil pressure `< 0` or `> 1500 kPa`).
   - Detects `STALE` if older than 2 hours from current time.
   - Preserves raw input string in `raw_input`.
4. Comprehensive tests in `tests/storage-ingestion.test.ts`.

### Non-Goals
- Do not connect to hosted Postgres or MongoDB.
- Do not introduce asynchronous message broker or Kafka.

---

## 4. Acceptance Criteria

- All repository interfaces implement typed async/sync methods.
- Ingestion correctly flags out-of-range sensor readings as `OUT_OF_RANGE`.
- State reset restores initial seed fixtures reliably.
- `tests/storage-ingestion.test.ts` passes 100%.
