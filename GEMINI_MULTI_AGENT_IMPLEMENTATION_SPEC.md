# Caterpillar Hackathon Starter — Gemini Multi-Agent Implementation Specification

> **Status:** implementation handoff specification; application implementation is not yet authorized.
>
> **Repository:** the current repository root (the directory containing this document).
>
> **Current repository state:** pre-event starter foundation with a tested asset-maintenance reference cartridge; no official challenge implementation exists.
>
> **Last reviewed:** 2026-09-21, Asia/Calcutta.

## 1. Purpose

This document turns the council-reviewed planning blueprint into an unambiguous contract that can be given to a Gemini coordinator to implement the eventual hackathon solution.

The problem statement, official rules, judging rubric, supplied data, and event constraints are not known yet. Therefore this document deliberately separates:

- decisions that are safe to lock before the reveal;
- fields that must be resolved after the reveal;
- optional capabilities that require evidence before activation; and
- exact implementation, review, QA, demo, and presentation gates.

The coordinator must not infer missing challenge details. It must stop before code creation when a hard-block field is unresolved.

## 2. Source-of-truth hierarchy

When two sources conflict, use this precedence:

1. Official hackathon rules, challenge statement, supplied datasets, judging rubric, and organizer clarifications.
2. The team-approved Challenge Compiler and Implementation Manifest described in this document.
3. Accepted or superseding Architecture Decision Records.
4. This implementation specification.
5. `PLANNING_A_TO_Z.md`.
6. `PRESENTATION_SYSTEM_PLAN.md` for presentation production details.
7. `HACKATHON_STARTER_PACK_PLAN.md` as a non-binding capability catalog.
8. Current `CONTEXT.md` for live status and active work; it may summarize but must not silently override accepted decisions.

Council evidence:

- `council-report-20260921-122900Z-qc00bdca0.html`
- `council-transcript-20260921-122900Z-qc00bdca0.md`
- Council decision SHA: `c00bdca0`

If source precedence does not resolve a conflict, the coordinator delegates an evidence-gathering task, creates or updates an ADR, and applies the decision policy in Section 20.

## 3. Hard stop before implementation

No application code, dependency installation, service provisioning, schema migration, provider account configuration, or deployment may begin until all of the following exist and contain no unresolved hard-block fields:

1. `planning/challenge-compiler.md`
2. `planning/implementation-manifest.md`
3. `planning/rules-and-provenance.md`
4. `planning/lock-trigger-register.md`
5. `CONTEXT.md`
6. A team-approved post-reveal implementation-readiness result

If any file is missing when the Gemini coordinator is invoked, it must:

1. inspect the source documents;
2. report the exact missing fields and why each blocks implementation;
3. propose the smallest planning action needed to resolve them; and
4. stop without writing application code.

It may delegate read-only research and planning checks, but it may not convert assumptions into implementation defaults.

## 4. Challenge Compiler contract

The Challenge Compiler is a one-page decision record completed immediately after the problem reveal. It must answer:

| Field | Required content | Hard block? |
|---|---|---:|
| Challenge ID | Organizer-provided identifier or a stable team ID | Yes |
| Exact statement | Verbatim problem statement with source | Yes |
| Official rules | URLs/files, version, accessed time, relevant constraints | Yes |
| Judging rubric | Criteria and weights, or explicit “not provided” | Yes |
| Primary user | One role, working environment, constraints, and authority | Yes |
| Decision/job | The exact operational decision or job being improved | Yes |
| Current failure | Measurable pain, risk, delay, waste, or uncertainty | Yes |
| Target outcome | Observable outcome and how it will be demonstrated | Yes |
| Permitted inputs | Data, APIs, media, documents, devices, and licenses | Yes |
| Hero behavior | One end-to-end behavior that proves the value | Yes |
| Supporting behaviors | Zero to two; each must support the hero behavior | Yes |
| Trust boundary | Evidence, uncertainty, confirmation, audit, and safety needs | Yes |
| Cartridge | Uptime/maintenance, inspection/safety, productivity/energy, or new | Yes |
| Success measures | Product, operational, technical, and demo measures | Yes |
| Non-goals | Explicit exclusions and prohibited scope | Yes |
| Cut order | Features removed first, second, and third if time collapses | Yes |
| Activated options | Trigger Later items with evidence and owner | Yes |
| Rejected options | Considered options not activated, with reason | No |

The hero behavior must fit this pattern:

    permitted source or user capture
      -> validation and normalization
      -> context and quality assessment
      -> deterministic baseline and/or activated analysis
      -> evidence-backed recommendation
      -> human review or confirmation
      -> work/audit record
      -> measurable outcome

## 5. Implementation Manifest contract

`planning/implementation-manifest.md` is the machine-readable-enough handoff to the coordinator. Use the following exact headings and values. A value may be `not-applicable`; it may not be silently omitted.

### 5.1 Identity

- Challenge ID
- Repository root confirmation: use the current Git/repository root and keep document references repository-relative
- Default branch
- Event start and submission deadline with timezone
- Team members, availability, and technical strengths
- Coordinator model and reasoning level
- Worker model and reasoning level
- Review model and reasoning level

### 5.2 Product

- Primary user
- Hero behavior
- Supporting behaviors, maximum two
- Golden demo path
- Measurable acceptance outcomes
- Non-goals
- Cut order

### 5.3 Stack

- Operating systems supported
- Runtime and exact version
- Package manager and exact version
- Web/application framework and exact version
- Repository layout
- Server/BFF choice
- Optional Python service: activated or disabled
- Relational or document/time-series persistence profile
- Hosted services activated
- Chart library, exactly one if required
- Test runner, browser test tool, linter, formatter, and type checker
- Local and hosted run commands

If these values are unresolved, the coordinator must commission bounded comparison spikes, receive evidence, record the ADR, and wait for approval where the choice is irreversible or materially affects eligibility.

### 5.4 Data

- Supplied source inventory and licenses
- Entity and identifier mapping
- Canonical units
- Timezone and timestamp policy
- Data quality states
- Raw-input retention policy
- Synthetic-data scenarios and seed
- Ground truth
- Reset mechanism
- Sensitive fields and retention

### 5.5 Activated capabilities

For every capability below record `activated` or `disabled`, evidence, owner, timebox, fallback, and cut condition:

- real authentication;
- Supabase/Postgres;
- MongoDB/time-series storage;
- Python/FastAPI analytics service;
- LLM decision-support;
- RAG or vector retrieval;
- ElevenLabs speech;
- mapping/geospatial provider;
- notifications/SMS;
- PDF/report generation;
- object/media storage;
- realtime subscriptions;
- deployment target.

### 5.6 Safety and compliance

- Competition prework ruling
- Third-party service ruling
- AI/tool-use ruling
- Data and media licenses
- Branding permission
- Privacy classification
- Consequential actions and confirmation text
- Human approver
- Offline/degraded behavior
- Prohibited physical-control actions

### 5.7 Delivery

- Active epic IDs
- Dependency DAG
- File ownership map
- Integration checkpoints
- Per-epic acceptance tests
- QA scenarios
- Demo reset procedure
- Presentation evidence outputs
- Freeze time

## 6. Product boundary

The reusable product kernel is:

1. **Identity and role context.** This may be a deterministic demo persona. Real login is optional and must be activated.
2. **Adaptable operational workspace.** The UI serves the selected decision or workflow. Do not assume a fleet dashboard.
3. **Data-to-action pipeline.** Inputs are validated, contextualized, analyzed, converted into a safe recommendation, confirmed where needed, recorded, and measured.

Build one proof-carrying hero behavior. Add no more than two supporting behaviors before the hero path is end-to-end, tested, resettable, and presentation-ready.

The product is decision support. It does not control physical machinery.

## 7. Scenario cartridges

The cartridges provide terminology, fixture ideas, and workflow patterns. They are not mandatory products.

### 7.1 Asset uptime and maintenance

- Candidate users: fleet manager, technician, planner.
- Candidate hero behavior: convert telemetry, fault events, history, and data quality into a prioritized inspection or maintenance recommendation.
- Candidate evidence: raw measurement, fault source, trend/rule, confidence, source freshness, recommended check, human decision, resulting work item.
- Candidate measures: detection lead time, precision, false alerts per asset-day, triage time, recommendation acceptance.

### 7.2 Technician inspection and safety

- Candidate users: operator, inspector, technician, safety lead.
- Candidate hero behavior: capture a structured observation under field constraints, retain it offline, synchronize it safely, triage it, and obtain human confirmation.
- Candidate evidence: observation, media/transcript, device time, sync state, policy/rule, severity rationale, reviewer and action.
- Candidate measures: completion time, missing-field rate, transcription correction rate, sync success, time to confirmed action.

### 7.3 Energy, utilization, and jobsite productivity

- Candidate users: site manager, dispatcher, sustainability or operations lead.
- Candidate hero behavior: compare actual operation with a baseline, identify avoidable idle/energy loss, and recommend a measurable scheduling or operating change.
- Candidate evidence: interval, source, unit-normalized series, baseline, comparison, confidence, recommendation, projected and observed impact.
- Candidate measures: idle ratio, energy/fuel intensity, utilization, schedule variance, estimated savings with labelled assumptions.

If the revealed problem does not fit, create a new cartridge while preserving the reusable kernel. Never rewrite the challenge to fit a prepared fleet narrative.

## 8. Architecture contract

### 8.1 Default posture

- Modular monolith first.
- Storage-neutral domain and provider interfaces.
- Deterministic local fixtures and replay are mandatory.
- External services sit behind adapters.
- One server/BFF unless the activated workload justifies a Python service.
- One chart library.
- Native platform HTTP facilities by default; do not add Axios without a recorded requirement.
- No microservices, message broker, agent framework, vector database, or multiple equivalent providers by default.

### 8.2 Conceptual modules

The codebase must keep these boundaries even if some modules are not activated:

- `identity`: persona, user, organization, membership, role, permission.
- `operations`: sites, assets, inspections, observations, plans, work orders.
- `ingestion`: source adapters, validation, normalization, replay, quality.
- `analytics`: deterministic rules/statistics and activated model adapters.
- `recommendations`: evidence, confidence, explanation, confirmation status.
- `workflow`: alerts, review, assignment, action, outcome.
- `audit`: immutable decision and state-transition records.
- `providers`: persistence, speech, LLM, maps, notifications, files.
- `demo`: seeded scenarios, reset, known-good replay, fallback status.

Imports must point inward toward domain contracts. Provider SDK types must not leak into domain entities or UI contracts.

### 8.3 Technology activation rules

| Technology | Default | Activate only when |
|---|---|---|
| Deterministic fixtures/replay | Required | Always |
| Relational conceptual model | Required | Always unless evidence disproves it |
| Supabase/Postgres | Disabled but preferred hosted profile | multi-user persistence/auth/storage/realtime is required and timed setup fits the event |
| MongoDB/time series | Disabled | data is append-heavy, high-volume, schema-variable and team/query evidence favors it |
| Next.js server/BFF | Candidate, not silently selected | team proficiency and challenge constraints support it |
| FastAPI | Disabled | Python-native ML, analytics, or streaming earns the extra service |
| LLM provider | Disabled | generative reasoning is essential to the hero behavior |
| pgvector/vector service | Disabled | semantic retrieval is required and structured/keyword retrieval is insufficient |
| LangGraph | Disabled | verified multi-step state/orchestration cannot be handled simply |
| ElevenLabs | Disabled | hands/eyes-busy, accessibility, language, or narration value is measured |
| Maps, Twilio, PDF | Disabled | activated workflow and rubric explicitly require them |

If a hosted profile consumes more than one-third of the expected build window in two representative drills, simplify it or promote only the proven reusable setup permitted by competition rules.

## 9. Domain and data contract

### 9.1 Entity inventory

Implement only activated entities, but preserve these meanings:

- Organization
- User
- Membership
- Role and Permission
- Site and Geofence
- Asset and AssetIdentifier
- Device and DataSource
- TelemetryMeasurement
- FaultEvent
- Inspection
- InspectionObservation
- MediaReference
- Recommendation
- MaintenancePlan
- WorkOrder
- Alert
- NotificationDelivery
- AuditEvent

### 9.2 Mandatory data rules

- Use stable internal IDs. Keep source identifiers and asset model designations separate.
- A value such as `CAT-336` is a model designation, not a unique asset ID.
- Never store an authentication token as a field on the User entity.
- Telemetry carries `observed_at`, `ingested_at`, numeric or typed value, unit, source, and quality.
- Timestamps are stored in UTC and rendered with an explicit user/site timezone.
- Raw permitted input is retained or hash-referenced according to the manifest; transformations retain lineage.
- Faults are events. Preserve standard, SPN/FMI or source code, controller/source, machine/model context, raw description, timestamps, and original payload reference.
- Latitude and longitude are separate validated fields or a proper spatial type, never an opaque combined string.
- Synthetic data is labelled in the UI, evidence register, and presentation.
- Seeds and fixture versions make test and demo scenarios repeatable.

### 9.3 J1939 policy

Use SAE J1939 concepts only when the challenge or licensed data supports them. Do not encode a universal Level 1/3/4 mapping for an SPN/FMI pair. Keep these fields separate:

- raw fault code;
- standard and source;
- source interpretation;
- application severity;
- severity policy version;
- confidence;
- recommended response;
- human disposition.

An OEM- or model-specific interpretation requires an authoritative permitted source. Otherwise label it simulated.

## 10. Data-to-action and Proof-and-Trust Harness

Every hero behavior must include:

1. deterministic fixtures with known ground truth;
2. a simple rule, statistical, or manual baseline;
3. input validation and explicit rejected/partial states;
4. source and transformation provenance;
5. quality and freshness assessment;
6. output evidence and explanation;
7. uncertainty or insufficient-evidence behavior;
8. human confirmation for consequential recommendations;
9. an audit event containing input reference, rule/model version, output, user decision, and outcome;
10. relevant error and false-alert metrics;
11. provider/offline fallback;
12. claims-ledger entries for every demo or deck assertion.

Do not use “AI-powered,” “predictive,” “real-time,” or quantified-impact language without a proof record and limitation.

## 11. UX and accessibility contract

The activated application must provide:

- a clear first-run or demo entry;
- visible persona/role context;
- one primary operational workspace for the hero behavior;
- loading, empty, partial-data, error, stale, offline, and permission-denied states;
- source, freshness, quality, and uncertainty where a recommendation appears;
- a review/confirmation step for consequential action;
- visible sync state for offline-capable workflows;
- a complete keyboard/touch path;
- screen-reader labels and managed focus;
- status communicated by text/icon as well as color;
- readable projector contrast and field-appropriate target sizes;
- captions/transcript for audio;
- no task that requires speech or hearing.

Use neutral industrial visual tokens. Do not use Caterpillar logos, trade dress, screenshots, protected product assets, or claim an “official” yellow without organizer-provided permission.

## 12. ElevenLabs voice contract

### 12.1 Activation

ElevenLabs is optional. Activate it only when the manifest identifies:

- the user constraint voice solves;
- exact intents or narration;
- measurable latency/accuracy/accessibility value;
- consent and retention policy;
- budget/rate limit;
- server-side credential design;
- text/touch fallback; and
- a cut condition.

### 12.2 Boundary

Expose provider-neutral application interfaces such as:

- speech input: audio plus locale -> transcript, confidence, timing, provider metadata;
- speech output: text plus approved voice/locale -> streamed or complete audio metadata;
- optional conversation session: bounded tools and explicit authorization.

ElevenLabs SDK types remain inside the provider adapter. Use server-side secrets. If browser access requires a temporary token or signed URL, mint it server-side with the narrowest scope and lifetime.

### 12.3 Safety and fallback

- Push-to-talk is the default for field input unless the manifest justifies another mode.
- Display the transcript before any consequential use.
- Require visual/touch confirmation for consequential actions.
- Never use a voice utterance alone to control equipment or finalize a high-impact action.
- Provide text entry and read-on-screen equivalents.
- On provider failure, quota exhaustion, denied microphone permission, high latency, or low confidence, fall back to text and preserve the draft.
- Recorded fallback audio must be labelled and must match current behavior.
- Do not clone a voice without explicit documented authorization.

### 12.4 Voice acceptance evidence

- time to first audio;
- end-to-end response latency;
- transcription correction rate on representative noisy samples;
- identifier error rate;
- cancellation and interruption behavior;
- permission-denied flow;
- provider outage and quota flow;
- no-secret-in-client verification;
- retention/deletion verification;
- text-equivalent completion.

## 13. Optional AI contract

Product LLM use is disabled until activated separately from the Gemini development agents.

If activated:

- select one provider and one exact model in the manifest;
- route calls through one application adapter;
- define a structured output schema;
- keep a deterministic baseline and mock;
- validate output before persistence or display;
- cite supplied evidence;
- state uncertainty and missing information;
- log latency, token usage, and estimated cost without logging sensitive content;
- guard retrieval against prompt injection;
- require human approval for consequential outputs;
- never present the system as a “Master Caterpillar Technician.”

Use the bounded role: “maintenance or operations decision-support assistant.” It may summarize evidence and propose safe checks; it may not claim authority, fabricate manuals, or control machinery.

RAG, embeddings, pgvector, a vector service, or LangGraph require individual activation evidence. Do not install them preemptively.

## 14. Offline and synchronization contract

Any field/offline workflow must define and test:

- client-generated local IDs;
- server IDs and ID reconciliation;
- observed, created, modified, and ingested timestamps;
- idempotency keys;
- ordered replay where ordering matters;
- retry with bounded backoff;
- record version or ETag;
- conflict detection and named resolution policy;
- attachment queue and resumable failure state;
- deletion/tombstone semantics;
- authentication expiry;
- user-visible pending/synced/failed/conflicted state;
- safe read-only or draft degradation.

Offline records must never silently overwrite a newer server version.

## 15. Security, privacy, safety, and provenance

- Keep secrets out of source, logs, screenshots, browser bundles, fixtures, and prompts.
- Maintain `.env.example` only after implementation is authorized; include names, never values.
- Use least privilege and exact CORS origins only when a real cross-origin deployment exists.
- Validate uploads, webhook signatures, replay/idempotency, size, type, and ownership.
- Treat location, employee identity, voice/audio, transcripts, inspections, and industrial data according to the manifest classification.
- Define microphone consent, transcript/audio retention, redaction, export, deletion, and demo sanitization.
- Record pre-event versus event-created work and third-party attribution.
- Record who confirmed each consequential action.
- Never connect the prototype to production machinery or send physical-control commands.
- Stale, poor-quality, unauthenticated, or unsynchronized state degrades to draft, read-only, or insufficient evidence.

## 16. Repository and concurrency policy

- Protect `main`.
- Use short-lived branches/worktrees named `gemini/{work-item-id}-{short-name}`, for example `gemini/E-04-baseline-analytics`.
- Do not create long-lived frontend, backend, or AI branches.
- One implementer owns one work item.
- Work items with overlapping files or mutable infrastructure run sequentially.
- Independent items run in parallel.
- Each worktree receives its own dependency directory/cache where required, Docker project name, database/schema, ports, seed, and environment file.
- Never point test agents at shared production-like mutable infrastructure.
- Merge only after implementation review, adversarial review, tests, and coordinator verification.
- Integrate vertically and frequently; do not wait until the end to combine layers.
- Preserve user-authored or pre-existing changes.

## 17. Epic decomposition and dependency DAG

The coordinator creates one work item per independently reviewable outcome. It may split these epics further, but it must not combine unrelated optional integrations.

### E-00 — Rules, manifest, and architecture freeze

- Inputs: official material and planning documents.
- Output: validated manifest, active epic DAG, ownership map, initial ADRs, no-code/blocker report.
- Code allowed: no.
- Completion: all hard blocks resolved and post-reveal gate approved.

### E-01 — Repository foundation

- Depends on: E-00.
- Output: activated project structure, pinned runtime/package manager, quality tools, environment schema, local commands, CI skeleton if permitted.
- Excludes: speculative providers and unused dependencies.

### E-02 — Domain contracts and deterministic fixtures

- Depends on: E-01.
- Output: activated entities, schemas/types, unit/time/provenance policy, seeded scenarios, ground truth, reset/replay mechanism.

### E-03 — Ingestion and storage profile

- Depends on: E-02.
- Output: validation, normalization, quality states, repository interfaces, activated persistence adapter, migrations if applicable.

### E-04 — Baseline analytics and recommendations

- Depends on: E-02 and required E-03 contracts.
- Output: deterministic baseline, evidence bundle, confidence/insufficient-data behavior, evaluation.

### E-05 — Operational workspace

- Depends on: E-02 contracts; may run with E-03/E-04 after contracts freeze.
- Output: hero UI states, role context, source/evidence display, accessible action/review flow.

### E-06 — Trust, audit, and offline behavior

- Depends on: E-02; integrates with E-03 through E-05.
- Output: confirmation policy, audit events, sync states/conflicts if activated, privacy and safety controls.

### E-07 — Hero-path integration

- Depends on: E-03 through E-06.
- Output: one complete source-to-outcome vertical slice, resettable demo scenario, end-to-end tests.

### E-08A — Authentication and hosted persistence

- Create only if activated.
- Depends on: E-02.
- Output: identity provider, memberships/roles, row/data authorization, hosted persistence and test isolation.

### E-08B — ElevenLabs voice

- Create only if activated.
- Depends on: E-05 interaction contract and E-06 safety contract.
- Output: server-side adapter, approved intents, transcript/review UI, text fallback, latency/accuracy/security tests.

### E-08C — Product LLM or retrieval

- Create only if activated.
- Depends on: E-04 evidence contract and E-06 safety contract.
- Output: provider adapter, schema validation, grounding/citations, deterministic fallback, evaluation and cost evidence.

### E-08D and later — Other external providers

- One separate epic per activated mapping, notification, media, report, or enterprise integration.
- Include provider sandbox, timeout/retry, mock/fallback, cost, privacy, and exit strategy.

### E-09 — Demo, evidence, and presentation integration

- Begins scenario/evidence planning alongside E-02; final integration depends on E-07.
- Output: demo script, fallback matrix, known-good reset, screenshots/video, metrics/claim cards, canonical Excalidraw exports, deck inputs.

### E-10 — Hardening and submission

- Depends on all active epics.
- Output: fixed critical findings, green QA scoreboard, tagged known-good build, offline backup, final docs and submission package.

## 18. Multi-agent execution protocol

### 18.1 Model assignments

- Coordinator: `gemini-3.1-pro-preview`, thinking level `high`.
- Implementation workers: `gemini-3.8-flash`, thinking level `medium`.
- Scenario-design and documentation workers: `gemini-3.8-flash`, thinking level `medium`.
- QA-execution workers: `gemini-3.8-flash`, thinking level `medium`.
- Adversarial code reviewers: `gemini-3.8-flash`, thinking level `high`.

Before dispatch, verify these exact IDs are available in the execution environment. Do not silently substitute a model. If unavailable, stop and ask for an updated explicit model map. The coordinator model must remain the higher-reasoning role.

Agent-model choice for development is separate from any LLM used inside the product.

### 18.2 Coordinator restrictions

The coordinator may:

- inspect files, diffs, logs, tests, and agent status;
- define tasks and dependency order;
- create worktrees through orchestration tools;
- compare output to the source documents;
- request fixes;
- consolidate reports; and
- make reversible decisions under Section 20.

The coordinator may not:

- implement or edit application code;
- write tests or fix findings itself;
- assign the entire system to one worker;
- accept a worker's self-reported tests without reading evidence;
- merge work that has not received adversarial review; or
- silently relax requirements.

All implementation, tests, migrations, documentation changes tied to behavior, and fixes are delegated.

### 18.3 Per-work-item lifecycle

1. Coordinator issues an exact brief with inputs, owned files, excluded files, contracts, dependencies, acceptance criteria, commands, and evidence format.
2. Scenario QA agent writes concrete scenarios before the implementer finishes.
3. Implementer works in an isolated worktree and reports files, decisions, tests, limitations, and commit.
4. Coordinator reads the diff and verifies it against requirements and claimed commands.
5. A separate adversarial reviewer attacks named risks for that item.
6. Confirmed findings go to the original implementer with file-and-line feedback.
7. Implementer fixes and reruns relevant tests.
8. QA executor runs scenarios against a real isolated stack.
9. Failures are classified as product bug, test bug, environment issue, or blocked external dependency.
10. Product bugs return to the owning implementer; test bugs return to the QA author.
11. Failed scenarios are rerun.
12. Coordinator accepts and integrates only after all required evidence is green or an explicit approved exception exists.

## 19. QA contract

### 19.1 Scenario-first requirements

For each work item, scenarios must cover:

- happy path;
- invalid/missing data;
- min/max and boundary values;
- authorization/role boundary;
- stale and low-quality data;
- dependency timeout, error, and malformed response;
- crash/restart or interrupted operation where relevant;
- idempotent retry and duplicate event;
- offline/sync conflict where relevant;
- accessibility and keyboard/touch completion;
- security/secret leakage checks;
- reset/replay;
- end-to-end hero arc;
- demo fallback.

Every scenario includes ID, preconditions, fixture version, exact actions or command, expected result, pass criteria, evidence location, owner, and status.

### 19.2 Real-stack execution

Run post-implementation QA against:

- the real activated database in an isolated test project/schema;
- real application processes;
- real migrations;
- real provider sandbox/test endpoints when safe and budgeted;
- no physical machinery or production operational systems.

External provider outages, cost limits, or missing organizer credentials may produce `blocked` only when the deterministic adapter/mock path is separately green and the blocker is documented with owner and resolution.

### 19.3 Required final scoreboard

Report:

- total scenarios;
- passed;
- failed;
- blocked with one reason per scenario;
- reruns performed;
- unresolved severity;
- test environment identifiers;
- command transcript/artifact paths;
- known limitations.

“Tests pass” without commands and evidence is not acceptable.

## 20. Decision and blocker policy

Use **decide and document** for reversible architecture or implementation decisions:

1. gather evidence;
2. compare at least two plausible options;
3. choose the lowest-complexity option satisfying the manifest;
4. record an ADR with consequences and revisit trigger;
5. flag the decision in the coordinator report.

Pause and ask the user before:

- violating or interpreting unclear competition rules;
- using data, branding, media, voices, or code with unclear rights;
- making an irreversible migration or destructive data operation;
- creating material external cost;
- weakening safety, privacy, authorization, or audit requirements;
- changing the hero behavior or success outcome;
- connecting to production equipment or systems;
- substituting unavailable coordinator/worker models.

Never let an agent fail or stall silently. Re-drive it with specific context, reduce the task, or respawn a replacement while preserving all evidence and decisions.

## 21. Quality bar

Each active work item requires:

- agreed acceptance criteria met;
- relevant unit tests green;
- contract and integration tests green;
- scenario QA executed;
- linter clean;
- formatter check clean;
- type checker clean;
- build clean;
- no high-severity adversarial-review finding;
- secrets and dependency checks appropriate to the stack;
- behavior documentation updated;
- ADR updated for deviations;
- evidence/claims register updated;
- reset and fallback verified where relevant.

No silent design deviation is allowed.

## 22. Demo and presentation outputs

Implementation is not complete until the hero path can supply:

- a deterministic setup/reset;
- one primary demo path;
- exact presenter actions and expected result;
- provider/offline failure fallback;
- source-to-recommendation evidence trail;
- metric snapshot with definition, method, sample size, and timestamp;
- claim card with source, confidence, limitation, and owner;
- architecture change note and current Excalidraw export;
- safe screenshot/media manifest;
- backup video/screenshots after demo freeze.

Intermediate reviews use 3–5 slides:

1. problem and current hypothesis;
2. selected decisions and architecture;
3. working evidence/demo moment;
4. risks, limitations, and asks;
5. next gate.

The final presentation follows `PRESENTATION_SYSTEM_PLAN.md`. The deck must never promise behavior the tested demo cannot show.

## 23. Coordinator deliverables

The final coordinator report must contain:

1. implemented hero and supporting behaviors;
2. active/rejected/cut epic list;
3. final architecture and accepted ADRs;
4. per-agent assignment, model, branch/worktree, commit, and status;
5. per-work-item review findings and resolution;
6. QA scoreboard and evidence paths;
7. build/lint/type/test commands and results;
8. provider, database, and deployment status;
9. safety/privacy/offline verification;
10. measured results versus claims;
11. known limitations and blocked items;
12. demo/reset/fallback instructions;
13. presentation artifacts;
14. exact repository state and known-good revision;
15. explicit deviations from this specification.

## 24. Filled Gemini coordinator prompt

Copy the prompt below only after the Hard Stop documents in Section 3 exist. Run it using `gemini-3.1-pro-preview` with high thinking.

---

# Multi-Agent Team Implementation — Coordinator Prompt

## Mission

Implement every active epic in `planning/implementation-manifest.md` for the challenge compiled in `planning/challenge-compiler.md`, inside:

the current repository root—the directory containing this specification and the other source documents.

This repository contains `src/core` and an isolated asset-maintenance reference cartridge. Treat the official challenge implementation as greenfield: reuse the core or cartridge only when competition rules and the approved manifest authorize it, and never assume the reference application satisfies the revealed problem.

Source-of-truth documents, in precedence order:

1. Official challenge/rules/rubric/data referenced by `planning/challenge-compiler.md`
2. `planning/challenge-compiler.md`
3. `planning/implementation-manifest.md`
4. Accepted ADRs referenced by the manifest
5. `GEMINI_MULTI_AGENT_IMPLEMENTATION_SPEC.md`
6. `PLANNING_A_TO_Z.md`
7. `PRESENTATION_SYSTEM_PLAN.md`
8. `HACKATHON_STARTER_PACK_PLAN.md`
9. `CONTEXT.md` for current status only

Read every applicable source before dispatching implementation. If any required file is missing, a hard-block manifest value is unresolved, or the post-reveal implementation gate is not approved, produce a blocker report and stop without writing application code.

## Your role: COORDINATOR ONLY

Act strictly as coordinator. Never implement, edit, test, or fix application behavior yourself. Delegate all implementation, behavioral documentation, test creation, QA, and fixes to worker agents.

- Create the dependency DAG from the active manifest epics.
- Spawn one implementation agent per independently reviewable work item. Never give the whole system to one agent.
- Run independent items in parallel.
- Run items with overlapping files, contracts not yet frozen, or shared mutable infrastructure sequentially.
- Before each dependent task, explicitly pass the finalized schemas, contracts, ADRs, commit IDs, and file paths from its dependencies.
- Give every agent exact owned/excluded files, acceptance criteria, test commands, and evidence format.
- Track status continuously.
- When a worker completes, read its diff, compare it to the source documents, inspect claimed command output, and verify that it changed only authorized files.
- If work has gaps, return it to the same implementer with specific file-and-line feedback. Do not fix it yourself.
- After implementation review, spawn a different adversarial code-review agent for that work item. Name the risks it must attack: contract drift, unsafe actions, authorization, data lineage, unit/time errors, retries/idempotency, offline conflicts, provider leakage, error handling, accessibility, tests, and activated item-specific risks.
- Route every confirmed finding to the original implementer, require fixes and reruns, and re-review.
- Merge only after review and QA gates pass.

## Model assignment

- Coordinator: `gemini-3.1-pro-preview`, thinking level `high`.
- Implementation workers: `gemini-3.8-flash`, thinking level `medium`.
- Scenario-design/documentation workers: `gemini-3.8-flash`, thinking level `medium`.
- QA-execution workers: `gemini-3.8-flash`, thinking level `medium`.
- Adversarial code-review workers: `gemini-3.8-flash`, thinking level `high`.

Set the model and thinking level explicitly on every spawn. Verify exact model availability first. Never silently substitute; if either model is unavailable, stop and ask for a revised explicit model map.

## QA — in parallel, not after

- For every work item, start a separate QA scenario-design agent while implementation is running.
- QA scenarios must exist before implementation completes.
- Cover happy paths, invalid/missing data, boundary values, authorization, stale/poor data, provider errors, crash/interruption, idempotent retries, duplicate inputs, offline conflicts, accessibility, security, reset/replay, end-to-end arcs, and demo fallback where applicable.
- Every scenario requires preconditions, fixture version, exact action/command, expected result, pass criteria, evidence location, and owner.
- After implementation, start QA-execution agents and run all scenarios against a real isolated stack: real activated database, migrations, application processes, and safe provider sandbox/test endpoints. Never connect to physical machinery or production operational systems.
- Record command transcripts and artifacts.
- Consolidate failures into a triage list. Root-cause each as product bug, test bug, environment issue, or blocked external dependency.
- Route product bugs to the original implementer and test bugs to the QA author.
- Rerun every failed scenario after correction.
- Report the final scoreboard: X passed / Y failed / Z blocked, with one explicit reason per blocked scenario.

## Engineering constraints

- Stack: use only the exact runtime, package manager, framework, database profile, libraries, test tools, deployment target, and versions approved in `planning/implementation-manifest.md`. Missing values are hard blockers.
- Architecture: modular monolith; storage-neutral domain/provider interfaces; deterministic fixtures/replay; provider SDK types may not leak into domain contracts.
- Product boundary: one hero behavior and at most two supporting behaviors.
- Data: UTC storage, explicit display timezone, observed and ingestion timestamps, units, source, quality, provenance, raw-input policy, seeded fixtures, and ground truth.
- Safety: advisory decision support only; no physical equipment control; human confirmation and audit for consequential actions; safe read-only/draft degradation.
- Authentication, Supabase/Postgres, MongoDB, FastAPI, product LLM/RAG, ElevenLabs, maps, notifications, PDF, object storage, realtime, and deployment are disabled unless marked activated in the manifest.
- ElevenLabs, if activated: server-side credentials, provider adapter, transcript review, visual/touch confirmation, retention policy, measured latency/accuracy, and complete text fallback.
- Product LLM, if activated: use only the exact provider/model in the manifest, structured validated outputs, evidence citations, uncertainty, deterministic fallback, prompt-injection controls, cost/latency logging, and human approval. Do not use the development-agent model as an implicit product dependency.
- HTTP client: native framework facilities unless an ADR justifies another library.
- Charts: exactly one library if needed.
- CORS: exact origins only when cross-origin deployment exists.
- Branding: neutral industrial styling unless official permission is recorded.
- Branches/worktrees: `gemini/{work-item-id}-{short-name}`, for example `gemini/E-04-baseline-analytics`; protected `main`; no long-lived frontend/backend/AI branches.
- Infrastructure isolation: unique Docker project, ports, database/schema, seed, and environment per concurrent work item. Never let agents or live tests share mutable infrastructure.
- Quality bar: unit, contract, integration and required end-to-end tests green; QA scenarios green; build/linter/formatter/type checker clean; no unresolved high-severity review finding; docs/ADR/evidence updated.
- No silent deviations from design. Record and report every deviation.

## Work-item protocol

Use the epic framework in `GEMINI_MULTI_AGENT_IMPLEMENTATION_SPEC.md` Section 17. Split epics into independently reviewable work items. Do not create optional E-08 work unless the manifest marks it activated.

For every worker brief include:

1. work-item ID and objective;
2. dependency commits/contracts;
3. owned and excluded files;
4. exact requirements and non-goals;
5. acceptance criteria;
6. required tests and commands;
7. security/safety/offline risks;
8. required documentation/evidence updates;
9. completion report format.

## Decisions and blockers

Decision mode: **decide + document** for reversible choices. Compare plausible options, choose the lowest-complexity compliant option, record an ADR with consequences/revisit trigger, and flag it in the report.

Pause and ask before unclear competition/IP/licensing questions, irreversible or destructive changes, material external cost, weakened safety/privacy/authorization, hero-scope changes, production-system connections, or model substitution.

Never let an agent fail or stall silently. Re-drive it with exact feedback, reduce the task, or respawn a replacement with its accumulated context and evidence.

## Completion report

Do not claim completion until all active epics satisfy the quality bar and the report contains:

- hero/supporting behaviors;
- active/rejected/cut epics;
- architecture and ADRs;
- agent/model/worktree/commit table;
- review findings and fixes;
- QA scoreboard with evidence;
- exact verification commands/results;
- provider/database/deployment status;
- safety/privacy/offline results;
- claims versus measurements;
- limitations and blockers;
- demo/reset/fallback instructions;
- presentation artifacts;
- known-good revision;
- deviations from source documents.

---

## 25. Model-reference note

Model IDs were verified against the official Gemini model documentation on 2026-09-21:

- Coordinator: `gemini-3.1-pro-preview`
- Workers: `gemini-3.8-flash`

Official references:

- [Gemini models](https://ai.google.dev/gemini-api/docs/models)
- [Gemini 3.8 Flash overview](https://ai.google.dev/gemini-api/docs/latest-model)
- [Gemini deprecations](https://ai.google.dev/gemini-api/docs/deprecations)

Model availability changes. The explicit preflight in the prompt is mandatory.
