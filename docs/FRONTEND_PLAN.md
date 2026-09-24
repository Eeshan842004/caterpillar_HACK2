# ShiftMate frontend build plan (operator app)

**Status:** slice 1 built and verified · 24 September 2026

**Verification (slice 1):** core engine 24/24 Vitest cases (spec worked examples TC-01…TC-16, TC-72, TC-73 and a J1 engine walk-through on the real demo seed); `tsc --noEmit` clean for content, core and operator; `expo export --platform web` builds (829 modules); a headless-Chrome keyboard-only walk-through of J1 passes 24/24 checks with no browser errors (pair → wrong PIN → sign-in → Guided briefing → acknowledge → board → start → Focus Mode → belt warning without exit advisory → ACK keeps hazard → Safe Exit Guard → secure clears it → idle prompt → truck wait → impact card with order unchanged → notify supervisor → proximity unavailable). Not yet verified on an Android device (E-02).
**Source of truth:** `TECHNICAL_SPEC.md` §4 (structure), §7 (screens, controls, state tables), §8 (logic), §11 (tasks). This plan only orders that work; it does not change behaviour.

## Stack (as specified)

- **Operator app:** Expo SDK 57 (React Native 0.86, React 19.2, expo-router), TypeScript 6.0, Android first, web build for judges and tests (spec §3.2, DR-04).
- **Domain engine:** `packages/core` — pure TypeScript with no React, Expo, timers, `Date.now` or `Math.random`; the app injects clock, IDs, storage and speech (DR-02, §4.2). Everything the operator sees is derived from the engine snapshot.
- **Content:** `packages/content` profiles, demo seed and demo history (already generated).
- **Console:** stays a separate Vite + React web app (spec DR-13) and is not part of this slice.

## Slice 1 — "J1 steps 1–9 on the web build, local mode" (this build)

| Spec task | What is built | Screens / modules |
|---|---|---|
| T03 (subset) | Core types, enums, clock, ids, time helpers, canonical JSON | `packages/core/src/types`, `util` |
| T06 | Signal store, machine state with debounce (§8.1) | `state/*` |
| T07 (subset) | In-memory ledger with append + correction resolution (§5.3.1); audience rules | `ledger/*` |
| T08 | Alert manager: lifecycle, grouping, repeats, escalation, speech queue, alert-budget counters (§8.3) | `alerts/*` |
| T09 | Seatbelt rules and Safe Exit Guard (§8.2), advisory only | `safety/seatbelt.ts`, `safety/safeExitGuard.ts` |
| T24 (subset) | Proximity levels, TTC, condition modifiers, monitoring-unavailable (§8.4) | `safety/proximity.ts`, `safety/conditions.ts` |
| T10 | Task state machine (§7.4.2), time accounting (§8.6.7), downstream impact preview (§8.6.9) | `tasks/*` |
| T11 (subset) | Baseline (§8.6.1), basis + range with the fallback band (§8.6.4), expected waiting (§8.6.5), live update (§8.6.6) | `estimate/*` |
| T12 | Idle tracker and classifier: required / reported / unexplained (§8.7) | `idle/*` |
| T13 (subset) | `ShiftEngine`: tick order (§8.16.3), commands, prompts with operating deferral, snapshot | `engine/*` |
| T14 (subset) | Live simulator driven by presenter toggles | `sim/liveSimulator.ts` |
| T15 | Expo app scaffold (SDK 57, expo-router, web + Android config) | `apps/operator` |
| T17 | No-touch input: keyboard map (§7.3), focus manager, web gamepad polling | `src/input/*` |
| T18 | EngineHost (1 s tick), store, ModeGuard (§7.4.1), presenter panel (F2) | `src/engine`, `src/navigation`, `src/sim` |
| T19 | Screens A0 (local only), A1 sign-in, A2 briefing, A3 task board with impact card, A4 task detail, A5 Focus, A6 Drive, A7 alert overlay, A7E Safe Exit Guard, A8 prompt sheet, status bar | `app/*`, `src/ui/*` |

**Done when:** on the web build, using only the keyboard, an operator can sign in as Ravi (PIN 1234), acknowledge the handover, see the estimate range with its basis, start trenching, and have the machine state drive Focus/Drive mode. Using the presenter panel:
- a belt-off while digging gives a WARNING with no exit advisory;
- door open plus belt-off while unsecured shows the Safe Exit Guard, which clears when the machine is secured;
- an idle prompts "Why the wait?", and answering "waiting for truck" moves the finish time and shows the downstream impact on task 2;
- a person approaching in rain triggers earlier than in dry weather, and a dropped feed shows "unavailable".

Core logic is covered by Vitest cases taken from the spec's worked examples (TC-01…TC-16, TC-72, TC-73).

## Deliberately deferred to later slices

| Deferred | Spec task | Why not in slice 1 |
|---|---|---|
| SQLite persistence (expo-sqlite; web needs COOP/COEP + wasm) | T16 | The engine writes through a `LedgerStore` port; slice 1 uses an in-memory store, and the SQLite adapter plugs into the same port |
| Server pairing, outbox, push/pull | T22 | The server side was just rebuilt; the app runs in "Local only" mode first |
| Incidents UI (A9), handover (A13), training (A10/A11), shift summary (A12), settings (A16), SOS | T25, T29, T30, T26, T41 | Built on the same engine snapshot in later slices |
| Voice (Vosk + DistilBERT ONNX) | T27, T28, T37 | Needs native builds and model files; every action already has its button path |
| Trained estimator artifact | T36 | The engine reads an artifact when present; until then basis = "fallback" with the 0.8–1.35 band (§8.6.4) |

## Verification

- `pnpm --filter @shiftmate/core test` — Vitest on the engine (runs in Node, no UI).
- `pnpm --filter @shiftmate/core typecheck` and `pnpm --filter @shiftmate/operator typecheck`.
- `pnpm --filter @shiftmate/operator export:web` — the web bundle must build.
- Manual: `pnpm operator:web`, then the "Done when" walk-through above with the keyboard only.
