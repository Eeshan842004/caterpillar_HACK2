# Hackathon Starter Pack — Reuse and Problem-Reveal Guide

## 1. What this repository is

This repository is a **challenge-neutral planning and engineering starter** plus one
**asset-maintenance reference cartridge**.

It is not an official Caterpillar submission and does not predict the problem statement.
The reference application proves that the process and reusable core can produce a working
industrial demo. The live challenge must still earn its own user, domain, data, stack
activations, evidence, and story.

## 2. Repository boundary

```text
.
├── planning/                         live reveal templates and durable decisions
├── src/core/                         challenge-neutral technical contracts
├── src/cartridges/
│   └── asset-maintenance/            replaceable reference implementation
├── examples/
│   └── asset-maintenance/            archived mock planning, QA, reviews and presentation
├── tests/
│   ├── core/                         reusable-core tests
│   └── cartridges/asset-maintenance/ reference-cartridge tests
├── PLANNING_A_TO_Z.md                planning governance
├── PRESENTATION_SYSTEM_PLAN.md       deck/evidence/rehearsal system
└── GEMINI_*                          implementation coordination contracts
```

The boundary is intentional:

- `core` may be reused when competition rules permit it.
- A `cartridge` is selected, adapted, created, or discarded after the reveal.
- `examples` teach the process but are never treated as current challenge truth.
- `planning` contains the only live Challenge Compiler, Manifest, rules and decisions.

## 3. Reusable now

### 3.1 Planning system

Reusable across likely challenges:

- one-page Challenge Compiler;
- Lock / Trigger / Evidence / Merge / Delete decisions;
- ADR format and decision rules;
- rules and provenance register;
- scenario-first QA and adversarial review workflow;
- evidence and claims discipline;
- demo reset and fallback planning;
- intermediate/final presentation production system;
- Gemini coordinator and work-item protocol.

Why reusable: these artifacts govern how the team turns uncertainty into a bounded,
verifiable build. They do not require a fleet, machine, login, dashboard, voice, or LLM.

### 3.2 Technical core

| Core area | Contract | Reuse reason |
|---|---|---|
| Evidence | `src/core/evidence` | quality, citations and audit records apply to any decision-support workflow |
| Determinism | `src/core/runtime` | fixed clocks and sequence IDs make fixtures and tests reproducible |
| Safety | `src/core/safety` | consequential actions require a target, title, human approver and timestamp |
| Offline queue | `src/core/offline` | generic payload queue models pending/synced/failed actions |
| Tooling | TypeScript, Vitest, ESLint, Prettier and build scripts | already exercised as a coherent baseline |

These modules intentionally contain no fleet, coolant, SPN/FMI, machine model, technician,
or work-order assumptions.

### 3.3 Reusable patterns, not necessarily reusable code

- modular monolith before microservices;
- provider SDKs behind adapters;
- deterministic fixture and reset profile;
- raw input plus normalized data and provenance;
- observed and ingested timestamps;
- quality/freshness states;
- deterministic baseline before advanced AI;
- evidence, confidence and insufficient-data output;
- human confirmation and audit record;
- text/touch equivalent for voice;
- neutral industrial visual language;
- known-good offline demo fallback.

## 4. Reference-only material

The following belongs to the asset-maintenance cartridge:

- fleet and asset entities;
- machine serial/model/category fields;
- telemetry parameters;
- J1939-style SPN/FMI fixtures;
- coolant and oil-pressure thresholds;
- maintenance recommendations and parts;
- technicians and maintenance work orders;
- fleet dashboard, asset selector and telemetry chart;
- asset-specific API route names;
- the mock challenge statement, rubric, QA evidence and deck.

Reuse it only when the revealed challenge genuinely requires the same concepts. Do not
rename an unrelated entity “asset” merely to keep the prepared code.

## 5. Known limitations of the reference cartridge

1. The React workspace uses the API-backed state path by default. Automated coverage is split
   between component/client tests and route-handler integration tests; a running-browser E2E
   suite has not yet been activated.
2. The offline queue is in memory and does not survive refresh/restart.
3. SHA-256 support proves tamper detection only if the original hash is retained; it is not
   an immutable external ledger or hash chain.
4. Default runtime IDs and timestamps are nondeterministic; deterministic replay requires
   the provided injected clock and ID generator.
5. Route-handler timing is not network/server load testing.
6. Authentication, Supabase/Postgres, ElevenLabs, product LLM/RAG, maps, notifications,
   media storage and hosted deployment are not active.
7. All operational and financial outcomes in the example are synthetic.

These are deliberate boundaries to state honestly, not reasons to add every integration
before the reveal.

## 6. What to do when the problem statement arrives

### Gate 0 — Capture authority before designing

Timebox: first 10–15 minutes.

1. Save the exact challenge statement and source.
2. Capture official rules, judging rubric, deadline and presentation format.
3. Record supplied data, APIs, devices, accounts and licenses.
4. Confirm which pre-event materials may be reused.
5. Update `planning/rules-and-provenance.md`.
6. Stop if an eligibility, licensing, branding or data-use question is unresolved and
   materially changes the build.

### Gate 1 — Compile the challenge

Timebox: 20–30 minutes.

Complete every row in `planning/challenge-compiler.md`:

- one primary user;
- one operational job/decision;
- current failure;
- measurable target outcome;
- permitted inputs;
- one hero behavior;
- at most two supporting behaviors;
- trust and safety boundary;
- non-goals and cut order.

Do not select technology during this discussion unless it changes whether the hero behavior
is feasible.

### Gate 2 — Select or create a cartridge

Timebox: 10–15 minutes.

Ask:

1. Does asset maintenance match the actual entities, workflow and evidence?
2. Does a planned inspection/safety or productivity/energy cartridge match better?
3. Is a new cartridge simpler and more honest?

Decision:

- **Strong match:** copy/adapt `src/cartridges/asset-maintenance`.
- **Partial match:** reuse only relevant submodules and replace domain language/rules.
- **No match:** leave the reference untouched and create
  `src/cartridges/{challenge-name}`.

### Gate 3 — Complete the Implementation Manifest

Timebox: 20–30 minutes.

Resolve `planning/implementation-manifest.md`:

- exact stack and versions;
- domain entities and identifiers;
- inputs, units, timestamps, quality and provenance;
- deterministic fixtures and ground truth;
- active capabilities;
- epic DAG, ownership and integration checkpoints;
- QA, demo reset, fallback and presentation outputs.

Every optional capability defaults to disabled.

### Gate 4 — Freeze contracts before parallel implementation

Produce:

- domain types and invariants;
- API/event boundaries;
- repository/provider interfaces;
- fixture schema and known ground truth;
- evidence and recommendation schema;
- confirmation/audit contract;
- error and degraded states;
- file ownership map.

Dependent agents receive these exact contracts and commit IDs. Do not parallelize work that
edits the same contracts.

### Gate 5 — Build one vertical slice

Implement this sequence first:

```text
real or synthetic permitted input
  -> validation and quality
  -> baseline analysis
  -> evidence-backed output
  -> human review/confirmation
  -> recorded outcome
  -> resettable demonstration
```

The UI and server should use the same application/use-case path when a server is activated.
Do not build separate “demo-only truth” and “API truth” without labelling the profiles.

Only after this path is green may the team add the first supporting behavior.

### Gate 6 — Activate optional capabilities from evidence

| Capability | Activate when | Required fallback |
|---|---|---|
| Authentication | identity, tenant separation or collaboration is judged | deterministic personas/read-only demo |
| Supabase/Postgres | persistence, multi-user, auth/storage/realtime is needed | local repository/fixture profile |
| MongoDB/time series | actual volume/schema/query shape earns it | structured local events |
| FastAPI/Python | Python-native ML/analytics materially helps | TypeScript baseline or offline job |
| Product LLM | generative reasoning is part of the hero behavior | deterministic rules/manual workflow |
| RAG/vector search | grounded semantic retrieval is required | structured/keyword retrieval |
| ElevenLabs | hands/eyes-busy, accessibility, language or narration value is measured | complete text/touch path |
| Maps | spatial reasoning or routing is judged | list/table/site metadata |
| Notifications | external delivery is part of the outcome | in-app alert |
| PDF/report | formal handoff/compliance output is required | print-ready view |

Each activation needs an owner, timebox, success measure, cost/quota, failure mode and cut
condition.

### Gate 7 — Produce evidence continuously

For every judged claim capture:

- claim text;
- source or test;
- method and environment;
- result and timestamp;
- limitations;
- screenshot/demo step;
- owner.

Do not wait until the final presentation to reconstruct evidence.

## 7. ElevenLabs reveal workflow

If voice is activated:

1. Define the real user constraint it solves.
2. Select exact input/output intents.
3. Keep keys server-side.
4. Implement provider-neutral speech input/output interfaces.
5. Display and allow correction of transcripts.
6. Require touch/visual confirmation for consequential action.
7. Preserve the draft when the provider fails.
8. Test microphone denial, noise, latency, quota, outage, interruption and retention.
9. Measure transcription correction rate and end-to-end latency.
10. Cut voice if it consumes the timebox without improving the hero behavior.

Voice should improve the workflow, not merely narrate a dashboard.

## 8. Definition of starter readiness

Before the event:

- [ ] Official prework rules are recorded when available.
- [ ] Live templates contain no invented problem statement.
- [ ] All document links are repository-relative.
- [ ] Core tests pass without importing an industrial cartridge.
- [ ] The asset-maintenance example remains isolated and clearly labelled.
- [ ] A non-fleet drill confirms the boundary.
- [ ] Clean install, test, type-check, lint and build succeed.
- [ ] No secrets or provider credentials are committed.
- [ ] The team knows the cut order and demo fallback policy.

After the reveal:

- [ ] Challenge Compiler is approved.
- [ ] Implementation Manifest contains no unresolved hard block.
- [ ] Rules and provenance are sourced.
- [ ] Cartridge selection is explicit.
- [ ] One hero behavior and at most two supporting behaviors are locked.
- [ ] Contracts and fixtures are frozen before dependent parallel work.
- [ ] Every activated provider has a mock/fallback and cut condition.
- [ ] QA scenarios exist before implementation completes.
- [ ] Claims, demo and deck use current evidence.

## 9. Team handoff statement

Use this summary when onboarding a teammate or implementation coordinator:

> Start with the live documents under `planning/`. Reuse `src/core` only if competition
> rules permit it. Treat `src/cartridges/asset-maintenance` and
> `examples/asset-maintenance` as a worked example, not current truth. After the official
> reveal, complete the Challenge Compiler, select or create a cartridge, activate only
> evidenced capabilities, freeze contracts, and build one tested source-to-outcome vertical
> slice before adding optional integrations.
