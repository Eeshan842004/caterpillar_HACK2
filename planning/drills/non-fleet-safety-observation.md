# Adaptation Drill — Offline Field-Safety Observation

> **Type:** desktop architecture drill, not an official challenge  
> **Purpose:** test whether the starter core works outside fleet telemetry  
> **Result:** PASS WITH KNOWN LIMITATIONS

## Mock prompt

Build a field-safety observation system for remote industrial sites. A worker must be able
to record a hazard while offline, attach evidence, receive a transparent priority
recommendation, and submit a consequential mitigation action for supervisor confirmation.

## Challenge Compiler summary

- Primary user: field inspector wearing gloves at a low-connectivity site.
- Operational job: turn an observation into a reviewed mitigation action.
- Hero behavior: capture observation -> validate required evidence -> assess quality and
  priority -> show recommendation and uncertainty -> supervisor confirms -> audit -> sync.
- Supporting behaviors: offline draft queue and visible conflict/sync state.
- Non-goals: automatic site shutdown, worker discipline decisions, facial recognition,
  equipment control, and unreviewed AI classification.

## Reuse test

| Existing part | Reuse? | Reason |
|---|---:|---|
| `src/core/evidence` | Yes | quality, evidence and audit contracts have no fleet terminology |
| `src/core/runtime` | Yes | injectable clock/ID boundaries support repeatable fixtures |
| `src/core/safety` | Yes | human confirmation applies to hazard mitigation |
| `src/core/offline` | Yes | generic payload queue accepts safety observations/actions |
| Test/build/tool configuration | Yes | challenge-neutral engineering foundation |
| Presentation and claims process | Yes | same evidence-to-slide workflow |
| Asset-maintenance types | No | assets, telemetry and SPN/FMI do not model observations |
| Coolant recommendation engine | No | rules and evidence are cartridge-specific |
| Fleet components and API names | No | the information architecture and language must change |
| Asset-maintenance fixtures | No | ground truth must represent hazards and mitigation |

## Proposed new cartridge

`src/cartridges/safety-observation/`

- `domain/types.ts`: Observation, HazardEvidence, MitigationRecommendation, Action.
- `domain/services/priority-engine.ts`: deterministic baseline with policy version.
- `fixtures/`: seeded hazards, media metadata, offline/conflict cases.
- `components/`: capture form, evidence review, priority explanation, confirmation.
- `adapters/`: local draft store and activated persistence adapter.

## Proof performed

`tests/core/reusable-core.test.ts` uses a hazard target rather than an asset and proves:

- generic human-confirmation validation;
- deterministic time and IDs through injection;
- generic offline action queueing;
- canonical audit hashing independent of snapshot key order.

## Known limitations

- The asset-maintenance UI consumes the API-backed state path by default, but the current
  automated suite does not exercise that path through a running browser.
- The generic offline queue is in memory. A challenge requiring refresh/restart durability
  must activate a durable browser or database adapter.
- The hash utility detects change only when the original hash is retained; it is not an
  immutable external audit ledger.
- This desktop drill measures architectural fit, not team reveal-to-scope elapsed time.

## Verdict

The reusable core survives a non-fleet prompt without renaming hazards as assets. The
asset-maintenance cartridge does not. This is the intended starter-pack boundary.
