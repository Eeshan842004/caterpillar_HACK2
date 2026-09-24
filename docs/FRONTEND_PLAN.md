# ShiftMate frontend delivery plan

**Status:** master roadmap; slice 1 built and verified · 24 September 2026

**Verification (slice 1):** core engine 24/24 Vitest cases (spec worked examples TC-01…TC-16, TC-72, TC-73 and a partial J1 engine walk-through on the real demo seed); `tsc --noEmit` clean for content, core and operator; `expo export --platform web` builds (829 modules); a headless-Chrome keyboard-only slice-1 walk-through passes 24/24 checks with no browser errors (pair → wrong PIN → sign-in → Guided briefing → acknowledge → board → start → Focus Mode → belt warning without exit advisory → ACK keeps hazard → Safe Exit Guard → secure clears it → idle prompt → truck wait → impact card with order unchanged → notify supervisor → proximity unavailable). This does not yet verify J1's correction, incident, training, handover or sync steps. Not yet verified on an Android device (E-02).
**Sources of truth:** `PRODUCT_PLAN.md` defines product scope and acceptance; `TECHNICAL_SPEC.md` defines behaviour, architecture and implementation tasks. This document maps both into deliverable frontend slices and does not change either source. `FRONTEND_DESIGN_PLAN.md` defines the visual direction, anti-template constraints, screen archetypes and design-quality gates for those slices.

## Scope and completion rule

The frontend includes both the operator app and the supervisor/trainer console. Slice 1 is only the first working vertical slice, not the complete product frontend. A capability is **complete** here only when:

1. every required screen and no-touch/button path is reachable;
2. its core, storage, server or content dependency is integrated rather than mocked, unless the product explicitly calls for simulation;
3. its product acceptance flow and mapped technical tests pass;
4. offline, machine-state gating, provenance, privacy and unavailable/error states are visible where applicable; and
5. the required web and Android checks have been recorded.

## Stack (as specified)

- **Operator app:** Expo SDK 57 (React Native 0.86, React 19.2, expo-router), TypeScript 6.0, Android first, web build for judges and tests (spec §3.2, DR-04).
- **Domain engine:** `packages/core` — pure TypeScript with no React, Expo, timers, `Date.now` or `Math.random`; the app injects clock, IDs, storage and speech (DR-02, §4.2). Everything the operator sees is derived from the engine snapshot.
- **Content:** `packages/content` profiles, demo seed and demo history (already generated).
- **Console:** a separate Vite + React web app (spec DR-13). It is outside slice 1 but inside this master frontend roadmap.

## Product coverage matrix

Status meanings: **Built** = integrated and verified for the stated platforms; **Partial** = some UI or core logic exists but product acceptance is not complete; **Planned** = assigned to a later slice; **Should** = attempted only after all Must gates pass.

| Product capability | Current status | Remaining frontend outcome | Delivery |
|---|---|---|---|
| M1 Sign-in and machine pairing | Partial | Server pairing/rebind, simulated key-fob path, remembered language and guidance level, offline operator list | Slices 2, 5 |
| M2 Briefing and handover receipt | Partial | Condition age/old state, machine notes, risk notes, read-aloud policy, acknowledgement persistence without resolution | Slices 2–4 |
| M3 Daily task board | Partial | Complete pause/block/resume/complete/output flows, completion criteria, assignment revision/source, pending reassignment and conflict states | Slices 2, 5 |
| M4 Task estimates and live finish time | Partial | Trained correction and P10–P90 artifact, factors, planner comparison, conditional ETA, why-changed view and retained original-vs-actual history | Slices 5, 6 |
| M5 Focus and Drive modes | Partial | Final spoken-information behaviour, complete status states, themes and Android readability/latency verification | Slices 5, 8 |
| M6 Seatbelt and Safe Exit Guard | Partial | Belt-unavailable detail, flapping follow-up visibility and private end-of-shift compliance summary | Slice 3 |
| M7 Proximity and working conditions | Partial | Direction/object variants, automatic snapshots, heat/wind/overspeed UI and forecast/operator condition inputs | Slices 3, 7 |
| M8 Alert lifecycle | Partial | Reviewed state, wrong/annoying feedback, review routing and complete incident linkage | Slice 3 |
| M9 Incident capture | Planned | A9 snapshot, source tags, button and voice report, confirm/correct, append-only history and console review | Slices 3, 4 |
| M10 Unusual behaviour | Partial | Engine-off estimate, overspeed/fuel/repeated-pattern findings, evidence state, correction and fair owner routing | Slice 3 |
| M11 Training hub | Planned | A10/A11 library, recommendations/reasons, condition prep, refreshers, defer/resume, history, help and launch content | Slice 4 |
| M12 Near-miss to scenario | Planned | Console draft/edit/approve and next-sync publication to operator recommendations | Slice 4 |
| M13 Voice and controls | Planned | Offline English/Hindi STT and intents, PTT, confirmation, clarification fallback, record correction and measured device latency | Slice 4 |
| M14 Handover authoring | Planned | A13 generated draft, audience, edit/remove reason, note/voice note, save, carry-forward and acknowledgement | Slice 4 |
| M15 Offline storage and sync | Planned | SQLite durability, offline-from-install shift, outbox, retry, conflicts, resume after crash and A14 status | Slices 2, 5 |
| M16 Machine profiles | Partial | Profile switching, full excavator/minimal haul-truck journeys, wheel-loader fallback and no-code-change acceptance | Slice 5 |
| M17 Supervisor/trainer console | Planned | C1–C5 roles, follow-ups, incidents, scenarios and handovers; C6/C7 remain Should | Slices 2–4, 7 |
| M18 Organiser replay and simulator | Partial | Compiled paired scenarios, provenance display and organiser replay that flags only expected rows | Slice 6 |
| M19 Evaluation results | Planned | Generated results artifacts with completed estimates, safety, alert-budget, usage, training, voice, propagation and organiser sections | Slice 6 |

### Should coverage after the Must gate

| Capability | Planned outcome | Delivery |
|---|---|---|
| S1 Language AI | Confirmable incident extraction, handover polish, scenario drafting and fact-grounded questions; template fallback always works | Slice 7 |
| S2 Tamil | Tamil UI per T47; Tamil voice remains an explicit gap requiring native-speaker/model validation and an approved implementation task | Slice 7 / new task |
| S3 Site tips | Eligible operator recording, task/area tagging, sync and playback | Slice 7 |
| S4 Personalisation | Evidence-counted private adjustment, widened early uncertainty, reset and opt-in sharing | Slice 7 |
| S5 SOS | A15 hold-to-send, delivery state, radio reminder and C7 alarm using the simulated LoRaWAN path | Slice 7 |
| S6 Fleet status | C6 view/filter/detail for 100 simulated machines | Slice 7 |
| S7 Model comparisons | Needs-review IsolationForest signal and clearly labelled LightGBM/SHAP evaluation comparison | Slice 7 |
| S8 Forecast | Cached forecast with age feeding conditions, briefing and condition prep | Slice 7 |
| S9 Incident replay | A17 secured-only timeline, one labelled deterministic counterfactual and focused training recommendation | Slice 7 |

## Slice 1 — partial J1 safety-and-work loop on the web build, local mode (built)

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

## Slice 1 deferrals

| Deferred | Spec task | Why not in slice 1 |
|---|---|---|
| SQLite persistence (expo-sqlite; web needs COOP/COEP + wasm) | T16 | The engine writes through a `LedgerStore` port; slice 1 uses an in-memory store, and the SQLite adapter plugs into the same port |
| Server pairing, outbox, push/pull | T22 | The server side was just rebuilt; the app runs in "Local only" mode first |
| Incidents UI (A9), handover (A13), training (A10/A11), shift summary (A12), settings (A16), SOS | T25, T29, T30, T26, T41 | Built on the same engine snapshot in later slices |
| Voice (Vosk + DistilBERT ONNX) | T27, T28, T37 | Needs native builds and model files; every action in the current slice has a button path |
| Trained estimator artifact | T36 | The engine reads an artifact when present; until then basis = "fallback" with the 0.8–1.35 band (§8.6.4) |

## Remaining delivery slices

### Slice 2 — persistence, pairing, sync and console foundation

**Tasks:** T05, T16, T20–T23. **Primary product coverage:** M1, M2, M3, M15 and the C1/C2 foundation of M17.

**Required execution order:**

1. Build T05 contracts and T20 server data model in parallel; T16 SQLite may proceed alongside them.
2. Start T21 only after both T05 and T20 pass their contract, schema and migration tests.
3. After T21, build T22 app pairing/sync and T23 console foundation in parallel.

T05 is a hard prerequisite, not optional infrastructure: it creates `packages/contracts`, the Pydantic mirrors and shared valid/invalid fixtures used to keep device and server payloads compatible. Slice 2 cannot pass its gate while those contracts are absent or failing.

- Replace the in-memory store with transactional SQLite and first-launch seed import.
- Add the shared TypeScript contracts, Python schema mirrors and cross-language fixtures before device API integration.
- Add server pairing/rebind, signed device requests, bootstrap, outbox push/pull and idempotent sync.
- Build A14 status/sync with online/offline state, pending-record count, sensor health and surfaced conflicts.
- Build role-authenticated console shell, C1 sign-in and C2 follow-ups with live updates.
- Gate: TypeScript and Python accept/reject the same contract fixtures; J1 through the reported truck wait runs on web and Android against the server; no-signal records queue and sync once; the site follow-up appears and can be resolved.

### Slice 3 — complete safety, incidents, findings and shift review

**Tasks:** T24–T26. **Primary product coverage:** M6–M10 and C3.

- Finish proximity object/direction handling, rain/dust/darkness modifiers, heat, wind and truck overspeed.
- Build A9 incident report with snapshots, source tags, read-back, confirm/correct and integrity state.
- Add incident review to C3 and route safety/trainer follow-ups without exposing private learning data.
- Build unusual-behaviour findings, owner/reason/evidence displays, correction propagation, wrong-alert feedback and the A12/My Review summary.
- Gate: product scenario pairs 1–5 and incident negation/correction pass; acknowledging never clears an active hazard; every finding has one justified owner or needs review.

### Slice 4 — voice, handover, training and near-miss learning loop

**Tasks:** T27–T31. **Primary product coverage:** M2, M9 and M11–M14 plus C4/C5.

- Add offline English/Hindi PTT recognition, deterministic high-consequence rules, ONNX intent fallback, top-three clarification and equivalent button paths.
- Build A13 handover authoring and C5 handover resolution, including audience, edit/remove reason, quick note and 20-second voice note.
- Build A10/A11 with complete English/Hindi launch packs, condition prep, reasoned recommendations, defer/resume, refreshers, history and trainer help.
- Build the reviewed-near-miss → editable C4 draft → approval → content-sync → operator recommendation loop.
- Gate: complete J1 steps 8–13 and J4; all launch intents pass the offline text/device checks; private answers never enter handover or console views.

### Slice 5 — assignment decisions, machine scaling and offline robustness

**Tasks:** T32–T34. **Primary product coverage:** M3–M5, M15 and M16.

- Complete reassignment request, notify-supervisor, pending/accepted/rejected and sync-conflict UI without silent task reordering.
- Switch profiles and run the haul-truck journey with Drive Mode, overspeed, dust proximity and truck-specific idle reasons; show an honest wheel-loader fallback.
- Resume shifts after reload/force-stop, verify retention and retry/backoff, and complete a full shift offline from install.
- Gate: J2 passes; switching profiles changes tasks, units, modes, hazards and content without code changes; reconnect produces no duplicate record.

### Slice 6 — data, trained models, organiser replay and evidence

**Tasks:** T35–T39. **Primary product coverage:** M4, M18 and M19.

- Ship and expose the trained estimator basis, range, factors, planner comparison and why-change explanation.
- Build the organiser replay view with visible provenance and expected-row checks.
- Run the full evaluation harness and include the generated results artifacts in the demo runbook.
- Gate: the app uses versioned production artifacts rather than test fixtures; `pnpm eval` fills every Must results section or records a specific not-run reason.

### Must gate — product-plan checkpoint

Before starting Should work, walk M1–M19 row by row and record the acceptance path, mapped tests and remaining exception for each. Every Must capability must be integrated and reachable; the release APK must launch; any cut requires the product owner's explicit decision and an update to this matrix.

### Slice 7 — approved Should features

**Tasks:** T31A and T40–T47. These start only after the Must gate passes.

- Implement only the approved Should items from the table above, following the technical-spec cut order if time is constrained.
- Complete localisation, offline/template fallbacks and explicit simulated/illustrative labels for every retained item.
- Gate: a Should feature is demo-visible only if its fallback, privacy boundary and failure state are also complete.

### Slice 8 — release verification and demo readiness

**Tasks:** T48–T51. **Applies to all product capabilities kept in scope.**

- Run web E2E, CI, Android release/device checks and two uninterrupted five-minute rehearsals.
- Verify the full product demo, not merely the Slice 1 walk-through, including correction, incident, training, offline/sync, handover, haul truck and results.
- Record device latency, startup, layout, audio, storage and missing-asset results; retain the recorded-video/offline-replay backup.

## Screen coverage

| Screens | Status and owning slice |
|---|---|
| A1–A8 and A7E | Partial/built in Slice 1; completed by Slices 2–5 |
| A9 Incident | Slice 3 |
| A10/A11 Training | Slice 4 |
| A12 Shift summary | Slice 3 |
| A13 Handover | Slice 4 |
| A14 Status and sync | Slice 2 |
| A15 SOS | Slice 7 (Should) |
| A16 Settings | Core language/guidance by Slices 2/4; personal reset/share in Slice 7 |
| A17 Incident replay | Slice 7 (Should) |
| C1/C2 | Slice 2 |
| C3 | Slice 3 |
| C4/C5 | Slice 4 |
| C6/C7 | Slice 7 (Should) |

## Cross-cutting frontend checklist

Every slice review must check the following where relevant; they cannot be postponed implicitly:

- **No-touch operation:** keyboard/controller focus, back, acknowledge, quick choices, hold timing and equivalent button paths.
- **Machine-state safety:** operating-state menu locks, prompt deferral, secured-only learning/reporting/replay, and no machine-control action.
- **Honest status:** stale/missing signals named as unavailable; conditional ETAs; fallback/insufficient-data basis; conflicts never silently overwritten.
- **Accessibility:** large targets and type, colour + icon + word, spoken critical information, night theme and high-contrast theme.
- **Responsive layout:** 10-inch landscape primary and 6-inch portrait supported without truncating critical content.
- **Localisation:** English/Hindi Must, no hard-coded operator text, language-specific audio availability and safe English fallback.
- **Privacy and provenance:** audience/source/origin visible where needed; private learning excluded from handover and console; simulated data labelled.
- **Reliability and performance:** ≤300 ms screen response, ≤1 s alert audio after trigger, ≤2 s offline voice command, ≤5 s cold start, crash-safe persistence and measured app/storage size.
- **Failure states:** offline-from-install, model/voice unavailable, old forecast, stale sensor, sync rejection/conflict, missing content/audio and server timeout.
- **Verification:** unit/contract/scenario tests plus keyboard web E2E and the applicable physical-Android check.
- **Design quality:** follow `FRONTEND_DESIGN_PLAN.md`; reject generic card grids, decorative pills, emoji icons, habitual uppercase labels and visual effects without an information role.

## Verification

- `pnpm --filter @shiftmate/core test` — Vitest on the engine (runs in Node, no UI).
- `pnpm --filter @shiftmate/core typecheck` and `pnpm --filter @shiftmate/operator typecheck`.
- `pnpm --filter @shiftmate/operator export:web` — the web bundle must build.
- Slice 1 manual: `pnpm operator:web`, then the "Done when" walk-through above with the keyboard only.
- Later slices add their mapped server, console, sync, content, voice, evaluation, E2E and Android checks; passing Slice 1 does not imply product-plan completion.
