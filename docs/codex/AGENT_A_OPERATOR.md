# Agent A — operator app (do now)

Read `AGENTS.md` first. You own `apps/operator/**` and `packages/core/**`. Work in this order; each item ends with its tests green.

Current state: core engine + Expo web app for J1 with an **in-memory** ledger and **Local only** pairing. `docs/FRONTEND_PLAN.md` lists what exists.

## A1. SQLite persistence (T16, §5.3 device schema, F13-R6)
- `npx expo install expo-sqlite`. Create `apps/operator/src/db/{database.ts,migrations.ts,SqliteLedgerStore.ts,repositories.ts,seed.ts,retention.ts}` exactly per §4.4 / §5.3 (migration 1, `PRAGMA user_version`, WAL).
- `SqliteLedgerStore` implements the core `LedgerStore` port: ledger row + outbox row in **one transaction**, FIFO persistence queue; the UI shows "Saved" only after the write resolves.
- Persist `device_config` (pairing), resume an open shift after reload (§7.2 navigation rules), 72 h sample retention (F13-R3).
- Web: Metro `wasm` asset + COOP/COEP headers (V-07); do not use `withExclusiveTransactionAsync`.
- **Done when:** reload the web app mid-shift → same shift, tasks and ledger count; the presenter "DB self-test" (100 appends, re-read) passes on web.

## A2. Findings + sync client (T22, §6.1–6.2, §8.8, §8.17)
- Core: `usage/findings.ts` — emit `inference/finding` (owner `site`, `idle_reported_wait`) when a site-delay reason is recorded, and `correction/finding` when it is corrected (§8.8, needed because the server now builds site-delay follow-ups **from findings**).
- Core: `sync/signer.ts` (HMAC-SHA256 canonical string, §6.1), `sync/outbox.ts` (type mapping, priorities §5.5, retry `5 s × 2^(n−1)` capped 300 s; jitter in the app), `sync/syncCore.ts` (`applyChange` for every change type in the §8.17 table). Add a signer test whose vector you compute with the server's algorithm (`server/tests/conftest.py::make_device_auth_headers`).
- App: `src/sync/*` — push every 10 s and after each insert, pull every 15 s, connectivity = `expo-network` + `/api/v1/health`; presenter "Simulate no signal"; A0 "Pair with server" (URL + 6-digit code; `TextInput` allowed only in A0); bootstrap import; A14 outbox counts, needs-review and rejected lists; A3 conflict badge.
- **Done when (against the local server):** pair with `100007`; J1 truck wait → `GET /api/v1/console/follow-ups` (as `sup.priya`) shows "Truck wait at … — 1 reports"; "actually, access blocked" moves it; "Simulate no signal" → N waiting → restore → 0 waiting, server shows no duplicate rows.

## A3. Incidents on the device (T25 device part, §7.4.5, §8.10, §8.11)
- Snapshot buffer (60 s pre / 30 s post), auto incident on proximity WARNING/CRITICAL and belt-move > 30 s, MARK_EVENT (hold Space 2 s → needs `listenToRelease`), A9 **button** report flow (type → object → place → contact), read-back, explicit OK; hash chain on append (§8.10, `canonicalJson` exists).
- **Done when:** presenter person approaching → incident; secure → "Report the near miss…" prompt → buttons → saved → pushed → server `chain_ok = true`, status `reported`.

## A4. Handover (T29 device part, §8.14, F12)
- A13 (OFF only): draft builder, quick notes, remove with reason, save → `handover_item/added` entries + `handover` bundle push; A3 "Add handover note"; task completion resolves linked items; briefing shows items from other devices (pull). Voice note recording waits for voice work.
- **Done when:** J1 steps 12–13 — blocked task, defect and near miss in the draft; Kumar (PIN 2468) acknowledges; items stay open; `GET /api/v1/console/handovers` shows the acknowledgement.

## A5. Summary, My review, Settings (T26 device part, §7.2 A3/A12/A16)
- A12 shift summary (OFF only): planned vs actual, active/waiting/break, alerts, private belt compliance. A3 "My review" sheet (own findings, operator-only, never synced). A16 (OFF only): guidance, theme, reset personal data.

## A6. Trained estimator + expected waiting (after Agent B delivers B1)
- When `packages/content/models/estimator.{excavator,haul_truck}.v1.json` exist, pass the class's artifact to the engine (`host.ts`); add the TC-10 parity test with B's golden file.
- Expected waiting (§8.6.5): join history completions to task types through `inference/estimate.payload.task_type` (field added by Agent B).
- Serve the web build under `/app` (`experiments.baseUrl`, DR-07) so the server can host it.

## Keep green
Core Vitest, all three typechecks, `export:web`. Re-run the keyboard-only J1 walkthrough (see `docs/FRONTEND_PLAN.md` "Verification") after A2 and after A4.
