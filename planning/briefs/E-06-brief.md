# Worker Brief — E-06: Trust, Audit, and Offline Behavior

- **Work-Item ID:** `E-06`
- **Assigned Worker Model:** `gemini-3.8-flash`, thinking level `medium`
- **Coordinator:** `gemini-3.8-flash`, thinking level `high`
- **Branch:** `gemini/E-06-trust-audit-offline`
- **Dependencies & Input Commits:** Depends on `E-02`, `E-03`, `E-04`, `E-05` (commit `a9a83ae`)

---

## 1. Outcome

A tamper-evident audit hashing verification engine and an offline-resilient synchronization manager that queues field supervisor actions when disconnected, prevents duplicate work orders via idempotency keys, and provides transparent sync status in the operational workspace.

---

## 2. Owned Files & Excluded Files

### Owned Files
- `src/domain/services/offline-sync.ts`
- `src/domain/services/safety-policy.ts`
- `src/components/OfflineSyncBanner.tsx`
- `tests/trust-audit-offline.test.ts`
- `planning/briefs/E-06-brief.md`

### Excluded Files
- Core domain entity definitions (Owned by `E-02`)
- API Route handlers (Owned by `E-07`)

---

## 3. Exact Requirements & Non-Goals

### Exact Requirements
1. **Safety Policy & Tamper Verification (`src/domain/services/safety-policy.ts`):**
   - Validates that every work order carries an authorized human approver signature.
   - Computes deterministic SHA-256 verification hash for each audit record to guarantee log immutability.
   - Rejects unconfirmed automated state changes.
2. **Offline Synchronization Service (`src/domain/services/offline-sync.ts`):**
   - Manages local client draft queue.
   - Assigns unique `idempotency_key` (UUIDv4) to every action.
   - Tracks sync state: `PENDING_SYNC`, `SYNCED`, `CONFLICT_RESOLVED`.
   - Reconciles queue with storage adapter upon reconnection without duplicate entries.
3. **Offline Sync Banner UI (`src/components/OfflineSyncBanner.tsx`):**
   - Displays real-time connectivity status (Online / Offline simulated toggle for demo).
   - Shows badge with number of pending items queued.
   - "Sync Queue" trigger button.
4. Comprehensive tests in `tests/trust-audit-offline.test.ts`.

### Non-Goals
- Do not build multi-server distributed consensus or Raft protocol.
- Do not introduce complex multi-master CRDTs beyond ordered event replay.

---

## 4. Acceptance Criteria

- Offline queue prevents duplicate creation when synced repeatedly (idempotency test passes).
- Tamper detection test verifies altered audit log fails hash verification.
- Offline banner renders in UI and updates pending item counts.
- `tests/trust-audit-offline.test.ts` passes 100%.
