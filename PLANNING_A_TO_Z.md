# Hackathon Starter Pack — A-to-Z Planning Blueprint

> **Council-reviewed baseline (2026-09-21).** This revision incorporates the five-lens council review recorded in `council-report-20260921-122900Z-qc00bdca0.html` and `council-transcript-20260921-122900Z-qc00bdca0.md` (decision SHA `c00bdca0`). The verdict was high-confidence and unanimous: prepare a compact, adaptable industrial decision-support spine rather than a prebuilt Caterpillar fleet product.

## 0. Council verdict and planning posture

### 0.1 What is genuinely reusable

The original three-part intuition is directionally sound, but it must not become an untested product assumption. The reusable kernel is:

1. **Identity and role context** — support a user, persona, or demo role; require real authentication only when the challenge, data, collaboration, or judging flow needs it.
2. **Adaptable operational workspace** — present the information and actions needed for the selected workflow; a machine dashboard is one cartridge, not the universal UI.
3. **Data-to-action pipeline** — capture or ingest, validate and contextualize, analyze, recommend a safe next action, record evidence, and measure the outcome.

This kernel should support one proof-carrying hero behavior and one or two simpler supporting behaviors. It must not presume that every problem is telematics, predictive maintenance, RAG, or voice-first.

### 0.2 Verified Caterpillar framing

Caterpillar is broader than “heavy machinery and IoT.” Its public portfolio and innovation work span construction and mining equipment, power and energy, digital connectivity, autonomy, safety, sustainability, workforce enablement, and financial services. VisionLink and Cat Inspect make connected-asset monitoring, faults, inspections, maintenance, mixed-fleet operations, and offline field workflows credible preparation areas; a prior official student hackathon also used VisionLink and asset-monitoring data. That evidence makes fleet operations a strong cartridge, not a prediction of the next problem statement.

Primary official references to keep in the evidence register:

- [Caterpillar innovation](https://www.caterpillar.com/en/company/about-caterpillar/innovation.html)
- [VisionLink](https://www.cat.com/en_US/products/new/technology/visionlink/visionlink/132082.html)
- [Cat Inspect](https://www.cat.com/en_US/products/new/technology/visionlink/visionlink/132081.html)
- [ISO 15143-3 / AEMP 2.0 API](https://digital.cat.com/apis/products/prod/iso-15143-3-aemp-20-api)
- [Prior Caterpillar student hackathon account](https://careers.caterpillar.com/en/life-at-caterpillar/career-blogs/hugos-day-in-the-life-as-an-intern/)
- [Caterpillar legal notices](https://www.caterpillar.com/en/legal-notices.html)

### 0.3 Governing rule

Every proposed artifact, dependency, integration, and feature is classified as one of:

- **Lock Now:** stable, low-cost foundation that is useful across likely challenges.
- **Trigger Later:** prepare the decision criteria, but activate only when challenge evidence justifies it.
- **Evidence Needed:** unresolved choice with a named experiment, source, owner, and deadline.
- **Merge:** fold duplicate material into the named canonical artifact.
- **Delete:** remove work that does not enable a decision, implementation, verification, demo, or presentation outcome.

No item is added merely because it might be useful.

## 1. Planning objective

Before implementation begins, create a compact operating system for the team. It must answer:

- What problem are we solving?
- For whom?
- What outcome will prove value?
- What is known, assumed, simulated, or undecided?
- What will the team build and deliberately not build?
- How will the system work?
- How will data, AI, voice, and external providers be used safely?
- How will the solution be tested and demonstrated?
- How will every teammate or coding agent get current context?
- How will decisions and scope changes be recorded?
- How will the final story, diagrams, deck, and demo be assembled?

This document defines the minimum artifacts, ownership, evidence thresholds, sequence, and implementation-readiness gate. It governs `HACKATHON_STARTER_PACK_PLAN.md`; where the older capability plan proposes a default that conflicts with this council-reviewed blueprint, this document takes precedence until an ADR supersedes it.

## 2. Planning principles

1. **One source of truth per subject.** Link to the canonical artifact rather than copying it.
2. **Plans must be executable.** Each important requirement should map to an owner, deliverable, and verification method.
3. **Facts and assumptions must be visibly different.** Never allow a speculative claim to become accepted context through repetition.
4. **Decisions need rationale.** Record alternatives and consequences, not only the final choice.
5. **Context must be concise enough to read.** Raw notes and research belong elsewhere.
6. **The final presentation is designed from day one.** Evidence, screenshots, architecture diagrams, and metrics should be planned as outputs of the work.
7. **The demo is a product requirement.** It receives its own scenarios, failure modes, tests, and owner.
8. **Unknown problem statements require modular planning.** Lock stable foundations; defer problem-specific choices.
9. **No implementation before the planning gate.** Scaffolding, dependencies, code, integrations, and environments wait until the agreed documents are ready.
10. **Every artifact has a budget and a decision.** Record the owner, decision enabled, time/size limit, freshness rule, and merge/delete condition.
11. **Offline and degraded modes are first-class.** Industrial workflows must remain legible and safe when connectivity, providers, or data quality degrade.
12. **Safety outranks novelty.** The prototype is decision support, not autonomous machine control; consequential actions require human confirmation and an audit trail.

## 3. Planning repository structure and artifact budget

### 3.1 Lock now: minimum planning pack

The council rejected creating a large documentation tree in advance. Before the challenge, maintain only this compact pack:

```text
.
├── CONTEXT.md                     # current truth and active handoffs
├── PLANNING_A_TO_Z.md             # planning policy and readiness gates
├── HACKATHON_STARTER_PACK_PLAN.md # capability catalog, governed by this file
├── PRESENTATION_SYSTEM_PLAN.md    # canonical deck/evidence/rehearsal plan
├── planning/
│   ├── challenge-compiler.md      # one-page reveal-to-scope decision sheet
│   ├── lock-trigger-register.md   # Lock/Trigger/Evidence/Merge/Delete table
│   ├── rules-and-provenance.md    # competition rules and pre-event provenance
│   ├── decisions.md               # ADR index or compact initial ADRs
│   ├── evidence-and-claims.md     # evidence, claims, measurements, limitations
│   └── risks-and-drills.md        # risks, mock-hack results, corrective actions
└── docs/
    ├── diagrams/                  # canonical Excalidraw sources and exports
    └── archive/                   # superseded material only
```

`README.md` and `AGENTS.md` become required when implementation is authorized. Separate requirements, threat model, data dictionary, test strategy, demo script, and slide artifacts are created only when the revealed challenge activates them or when the corresponding section outgrows its compact register.

### 3.2 Challenge Compiler

`planning/challenge-compiler.md` is the first planning artifact to complete when rules or a problem statement arrive. Keep it to one page and require:

| Decision | Required answer |
|---|---|
| Problem | What exact operational decision or job is failing today? |
| User and environment | Who acts, where, under what noise/connectivity/safety constraints? |
| Outcome | What changes for the user or operation, and how can it be demonstrated? |
| Inputs | What data is supplied, permitted, credible, and available during the event? |
| Hero behavior | What single end-to-end behavior proves the core value? |
| Supporting behaviors | Which one or two behaviors make the hero flow usable? |
| Trust | What evidence, uncertainty, confirmation, and auditability are required? |
| Constraints | Rules, time, team skills, devices, network, privacy, and judging rubric. |
| Cartridge | Uptime/maintenance, inspection/safety, productivity/energy, or genuinely new. |
| Activation decisions | Which Trigger Later items have now earned implementation? |
| Non-goals | What will not be built in this event? |

The compiler must produce an MVP statement, a golden path, measurable success criteria, an explicit non-goal list, and a signed-off activation set before implementation planning.

### 3.3 Artifact budget

Every artifact must state: owner, decision enabled, audience, last-updated time, time/size budget, and merge/delete trigger. Default limits are one page for live planning sheets, one screen for `CONTEXT.md` essentials, and one source of truth per subject. If an artifact cannot name a decision or deliverable it enables, merge or delete it.

### 3.4 Trigger-later document catalog

Create a separate artifact only when the named condition is met:

| Category | Possible artifact | Activation condition |
|---|---|---|
| Governance | team charter, ownership, communication or change log | team size/complexity cannot be managed in `CONTEXT.md` |
| Challenge | rules, rubric, personas, research, glossary | official material arrives or terminology/rules affect scope |
| Product | brief, requirements, traceability, journeys, metrics | the revealed problem and judged requirements are known |
| Experience | information architecture, wireflows, accessibility, voice | the activated hero flow requires design decisions |
| Architecture | system/data/deployment/trust views and integration catalog | the selected vertical slice makes a view decision-relevant |
| Data and AI | dictionary, contracts, evaluation/model card, responsible AI | supplied data or activated analytics/AI needs formal treatment |
| Security | threat model, privacy, classification, abuse cases | data sensitivity, identity, uploads, voice, AI, or external providers activate risk |
| Delivery | implementation/test/release/runbooks | implementation is authorized and the item enables assigned work |
| Demo | script, fallback matrix, rehearsal and judge Q&A | the MVP and event format are locked |
| Presentation | story, slides, notes, evidence, media | use `PRESENTATION_SYSTEM_PLAN.md` as the canonical system |

Do not create files merely to fill categories. An artifact requires an owner, a decision or delivery outcome, a time/size budget, and a deletion or consolidation rule. Empty or duplicated documents create false confidence and must be deleted or merged.

## 4. Root-level documents

### 4.1 `README.md` — entry point

Audience: judges, new teammates, mentors, and reviewers.

Required sections:

- One-sentence product summary.
- Current status: planning, building, demo-ready, or archived.
- Problem and primary user.
- Value proposition.
- Feature summary.
- Architecture snapshot.
- Setup and run instructions, once implementation begins.
- Demo instructions.
- Repository map.
- Known limitations.
- Team and attribution.
- License and third-party acknowledgements.

The README should remain concise and link to deeper documents.

### 4.2 `CONTEXT.md` — shared live context

Audience: every human and coding agent starting or resuming work.

Purpose: communicate the minimum current truth needed to make a safe, aligned contribution.

Recommended structure:

```markdown
# Current Context

Last updated: YYYY-MM-DD HH:MM TZ
Updated by: name
Context version: N

## Current phase
Planning / implementation / hardening / demo freeze

## North-star objective
One short paragraph.

## Current problem framing
User, pain, desired outcome, constraints.

## Current scope
In scope, out of scope, stretch goals.

## Current golden path
Numbered end-to-end workflow.

## Locked decisions
Short summary with links to ADRs.

## Working assumptions
Only assumptions currently affecting work.

## Current architecture
Short description and diagram link.

## Active work
Owner, task, status, dependencies.

## Risks and blockers
Top items only, with owners.

## Next decisions
Questions that genuinely need resolution.

## Verification status
What is proven, unverified, mocked, or simulated.

## Read next
Links to the few documents needed for current work.
```

Context rules:

- Keep it short enough to read in under five minutes.
- Update it after a meaningful scope, architecture, ownership, or status change.
- Do not paste meeting transcripts, research dumps, or implementation logs.
- Link to ADRs instead of duplicating decision rationale.
- Include an explicit timestamp and editor.
- Remove stale items rather than accumulating history; history belongs in the change log.
- Clearly label simulated, mocked, planned, and implemented functionality.
- Never store secrets, access tokens, private datasets, or personal data.

### 4.3 `AGENTS.md` — contribution instructions

Audience: coding agents and developers working in the repository.

Recommended content:

- Mandatory read order: `CONTEXT.md`, relevant ADRs, relevant feature plan.
- Approved commands and package managers.
- Formatting, linting, testing, and build gates.
- Repository conventions.
- File ownership or protected areas.
- Security rules for secrets and customer data.
- How to update context and ADRs.
- Requirement for tests and documentation with changes.
- Rules for generated files and diagrams.
- Demo-freeze restrictions.
- What not to change without an ADR.

Keep universal project truth in `CONTEXT.md`; keep operational contribution rules in `AGENTS.md`.

### 4.4 Master-plan relationship

- `HACKATHON_STARTER_PACK_PLAN.md` describes the reusable product and technical capability space.
- `PLANNING_A_TO_Z.md` describes how planning artifacts are created and governed.
- `PRESENTATION_SYSTEM_PLAN.md` defines the evidence, asset, deck, review, and rehearsal system for intermediate and final presentations.
- `CONTEXT.md` describes current truth.
- ADRs explain why durable decisions were made.
- The implementation plan converts accepted scope into sequenced work.

## 5. Architecture Decision Records

### 5.1 ADR template

```markdown
# ADR-NNN: Decision title

- Status: proposed | accepted | superseded | rejected | deprecated
- Date: YYYY-MM-DD
- Owners: names
- Decision deadline: optional
- Supersedes: ADR link, if applicable
- Related requirements: IDs

## Context
What forces, constraints, unknowns, and quality attributes matter?

## Decision drivers
- Driver 1
- Driver 2

## Considered options

### Option A
- Description
- Benefits
- Costs and risks

### Option B
- Description
- Benefits
- Costs and risks

## Decision
What was selected?

## Rationale
Why does it best satisfy the drivers?

## Consequences
- Positive
- Negative
- Follow-up work

## Validation
What evidence will confirm or invalidate the decision?

## Revisit trigger
What event, metric, or new information should cause reconsideration?
```

### 5.2 ADRs worth preparing or deciding

Do not pre-create 25 empty ADRs. Record compact provisional decisions in `planning/decisions.md`, then promote a decision to its own ADR only when it has meaningful alternatives, lasting consequences, or a revisit trigger.

**Lock Now ADRs**

1. Reusable architecture boundary: modular monolith first, optional Python analytics service only when the selected workload requires it.
2. Storage-neutral domain contracts, deterministic fixtures/replay, units, timestamps, provenance, and quality policy.
3. Human-in-the-loop safety, consequential-action confirmation, and no physical machine control.
4. Offline/degraded behavior and demo reset/fallback strategy.
5. Secrets, provider-adapter, documentation, diagram, and evidence conventions.

**Trigger Later ADRs**

1. Hosted persistence and authentication: Supabase/Postgres is the leading activation profile; do not make it a baseline dependency before the challenge.
2. MongoDB/time-series storage: activate only for demonstrably high-volume, append-heavy, highly variable telemetry and a team/query pattern that benefits.
3. Separate FastAPI service: activate only when Python-native ML, streaming, or analytics materially earns the operational cost.
4. AI retrieval/orchestration: activate RAG, pgvector, LangGraph, or a vector service only when grounded semantic retrieval or multi-step state is part of the hero behavior.
5. ElevenLabs voice, mapping, notifications, generated PDF reports, object storage, and deployment vendor: decide only from user constraints, rubric, and demo evidence.
6. Final framework, charting library, runtime versions, and test stack: decide from team proficiency and event constraints; use one chart library and native `fetch` unless a demonstrated need justifies Axios.

Each Trigger Later ADR must name its activation evidence, cheapest validation, fallback, and deactivation condition.

### 5.3 ADR anti-patterns

- Recording a decision after implementation solely to justify it.
- Listing only the selected option.
- Treating preferences as requirements.
- Omitting negative consequences.
- Allowing accepted ADRs to be silently contradicted by code.
- Editing history when a decision changes; supersede it with another ADR.

## 6. Requirements and traceability

### 6.1 Requirement categories

- Product and user requirements.
- Functional requirements.
- Data requirements.
- Voice and accessibility requirements.
- AI/analytics requirements.
- Security and privacy requirements.
- Reliability and performance requirements.
- Demo and judging requirements.
- Operational/deployment requirements.
- Documentation and handoff requirements.

### 6.2 Requirement format

Each requirement should have:

- Stable ID, such as `FR-012` or `SEC-004`.
- Clear statement using “must,” “should,” or “may.”
- Rationale.
- Source: challenge rule, judge criterion, user need, assumption, or team choice.
- Priority.
- Owner.
- Dependencies.
- Acceptance criteria.
- Verification method.
- Status.
- Links to design, code, tests, and evidence when available.

### 6.3 Traceability matrix

Recommended columns:

| Requirement | User/rubric need | Design | ADR | Planned work | Test/evidence | Demo step | Status |
|---|---|---|---|---|---|---|---|

The matrix prevents impressive but irrelevant work and exposes claims with no verification.

## 7. Assumption, question, and evidence management

### 7.1 Assumptions register

Columns:

- ID.
- Assumption.
- Why it matters.
- Confidence.
- Impact if false.
- Validation method.
- Owner.
- Deadline.
- Status and evidence.

Classify assumptions as user, data, technical, business, operational, judging, legal/privacy, or schedule.

### 7.2 Open-questions register

Each question should include:

- Decision it blocks.
- Best current default.
- Who can answer it.
- Deadline.
- Consequence of waiting.

Do not let unresolved questions stop unrelated work. Use reversible defaults for low-impact uncertainty.

### 7.3 Evidence register

Track evidence used in product claims and the final deck:

- Claim.
- Source.
- Date accessed.
- Strength and limitations.
- Permission/licensing notes.
- Slide or demo step using it.
- Owner.

Separate measured prototype results, public research, challenge-supplied data, and simulated estimates.

## 8. Product planning artifacts

### 8.1 Product brief

- Product name and one-line description.
- Primary user and buyer/stakeholder.
- Problem and current workflow.
- Proposed intervention.
- Unique value.
- Success metrics.
- Major risks.
- Explicit non-goals.

### 8.2 Persona and jobs-to-be-done sheet

For every important user:

- Role and environment.
- Goals.
- Current workflow.
- Information available.
- Pain, risk, and workarounds.
- Physical constraints: noise, gloves, connectivity, sunlight, mobility.
- Trust and approval needs.
- Job-to-be-done statement.

Likely industrial roles include operator, technician, site supervisor, fleet manager, safety manager, planner, dealer support representative, and executive.

### 8.3 Pre-event scenario cartridges

Prepare concepts and synthetic fixture specifications for no more than three cartridges. They are planning lenses, not preselected products:

| Cartridge | Likely users | Representative hero behavior | Reusable proof |
|---|---|---|---|
| Asset uptime and maintenance | fleet manager, technician, planner | turn telemetry/fault/history into a prioritized, evidence-backed inspection or maintenance recommendation | ingestion, quality checks, time series, anomaly/rule, recommendation, work/audit record |
| Technician inspection and safety | operator, inspector, safety lead | capture a structured observation in the field, work offline, classify/triage it, and obtain human confirmation | offline form/media/voice capture, sync state, evidence, severity policy, approval |
| Energy, utilization, and jobsite productivity | site manager, dispatcher, sustainability lead | compare operations, identify avoidable idle/energy loss, and recommend a measurable scheduling or operating change | aggregation, baseline, comparison, explanation, projected impact |

The reveal may select none of these. When that happens, reuse the kernel and create a fourth challenge-specific cartridge rather than forcing the problem into fleet language.

### 8.4 Use-case catalog

For each use case:

- ID and name.
- Actor.
- Trigger.
- Preconditions.
- Happy path.
- Alternatives and exceptions.
- Data required.
- Output/action.
- Safety and authorization implications.
- Value metric.
- Demo suitability.
- Reusable component mapping.

### 8.5 Scope document

Maintain four explicit lists:

- Must demonstrate.
- Must support behind the demo.
- Stretch goals.
- Out of scope.

Also define a deletion order: which features are removed first if time collapses.

### 8.6 Success-metrics tree

Connect:

```text
Business/mission outcome
  -> operational outcome
    -> user behavior
      -> product signal
        -> technical measurement
```

Example:

```text
Reduce unplanned downtime
  -> identify degradation earlier
    -> technician reviews high-risk assets daily
      -> risk alerts are opened and acted upon
        -> lead time, precision, false alerts per asset-day
```

## 9. UX and design planning

### 9.1 Information architecture

Define:

- Primary navigation.
- Role-specific views.
- Global versus contextual actions.
- Search and filter behavior.
- Entity relationships.
- Deep-link strategy.
- Empty and first-run experience.

### 9.2 User journeys

At minimum, diagram:

- First visit and demo entry.
- Import data to actionable insight.
- Alert triage to confirmed action.
- Guided inspection.
- Voice question to cited answer.
- Failure/offline fallback.

### 9.3 Screen inventory

For each proposed screen capture:

- User goal.
- Required information.
- Primary action.
- Empty/loading/error/offline state.
- Permissions.
- Voice behavior.
- Analytics event.
- Demo importance.

### 9.4 Design system decisions

- Color tokens and industrial brand neutrality.
- Typography and density.
- Spacing and layout grid.
- Severity/status colors and redundant labels/icons.
- Chart palette.
- Table behavior.
- Form and validation patterns.
- Voice states.
- Projector and sunlight legibility.
- Dark mode requirement.
- Motion policy.

### 9.5 Accessibility plan

- Keyboard navigation.
- Screen-reader labels.
- Focus management.
- Caption/transcript equivalence.
- Color-independent status communication.
- Target sizes for tablet/glove use where relevant.
- Reduced-motion support.
- Plain-language mode.
- No workflow requiring speech or hearing.

## 10. Voice experience plan

**Council classification: Trigger Later.** Caterpillar publicly demonstrates voice-oriented technician/operator assistance, so voice is domain-plausible. That does not make ElevenLabs a Caterpillar requirement or endorsement. ElevenLabs remains an optional provider behind a server-side adapter, and every voice workflow must have a complete text/touch equivalent.

### 10.1 Decide the purpose before the provider

Specify which user constraint voice solves:

- Hands occupied.
- Eyes occupied.
- Faster narrative capture.
- Audible urgency.
- Multilingual access.
- Accessibility.
- Conversational information gathering.

### 10.2 Voice modes

- Narration/read-aloud.
- Push-to-talk command.
- Dictation.
- Guided workflow.
- Conversational copilot.
- Generated briefing.
- Training simulation.

### 10.3 Voice interaction specification

For every voice intent define:

- Example phrases and language variants.
- Required parameters.
- Clarification policy.
- Read-only, draft, or consequential classification.
- Confirmation wording.
- Visual equivalent.
- Timeout and cancellation behavior.
- Error and provider fallback.
- Transcript/audio retention behavior.

### 10.4 ElevenLabs planning decisions

- TTS only, STT + TTS, or ElevenLabs conversational agent.
- Selected voice and permitted usage.
- Model selection criteria: latency, quality, language, cost.
- Server-side secret handling.
- Signed URL or temporary token flow.
- Client and webhook tool catalog.
- Tool authorization and idempotency.
- Credit limit and rate limit.
- Consent and retention.
- Mock/recorded fallback.
- How to measure time to first audio and transcription quality.

Activate ElevenLabs only when the chosen user works hands-busy/eyes-busy, narration or multilingual output materially improves the hero path, or the judging rubric rewards it. Do not activate it as decoration. The planning default is a provider-neutral `speech input` / `speech output` boundary, one selected provider, and a deterministic text or prerecorded fallback. Never expose a provider key in the browser, clone a voice without documented authorization, or allow a voice utterance alone to execute a consequential action.

OpenAI Whisper, Google Speech-to-Text, or any second provider is not a parallel default. Compare providers only if the activated use case has a measured accuracy, language, latency, privacy, or cost requirement that the first choice cannot satisfy.

### 10.5 Voice pre-mortem

Plan for:

- Noisy venue.
- Poor microphone.
- Permission denied.
- Network latency.
- Provider outage.
- Credit exhaustion.
- Incorrect language detection.
- Misheard identifiers.
- Speaker feedback/echo.
- Accidental consequential request.
- Judge interrupting the agent.

## 11. Architecture planning

### 11.0 Council-approved architecture posture

Plan a **modular monolith with storage-neutral contracts and deterministic local fixtures/replay**. It is the reusable industrial spine, not a prebuilt full application. Its conceptual path is:

```text
source/capture -> validate + normalize -> contextualize -> analyze
               -> evidence-backed recommendation -> human decision
               -> work/audit record -> outcome measurement
```

Keep clear module boundaries for identity/roles, operational entities, ingestion, analytics, recommendations, workflow, audit/evidence, and provider adapters. A Next.js server/BFF is sufficient for the default web path; a separate FastAPI service is activated only when Python-native analytics or ML earns it. Avoid microservices, message brokers, vector databases, agent frameworks, and multiple providers until challenge evidence crosses their trigger.

### 11.1 Quality attributes

Rank what matters for the eventual challenge:

- Demo reliability.
- Adaptability.
- Time to implement.
- Explainability.
- Security/privacy.
- Offline behavior.
- Latency.
- Scalability.
- Maintainability.
- Cost.

Architecture tradeoffs should refer back to this ranking.

### 11.2 Technology decision matrix

| Choice | Current verdict | Activation evidence |
|---|---|---|
| Local deterministic fixtures/replay | Lock Now | universal demo reliability and repeatable testing |
| Relational domain model | Lock Now conceptually | operational entities and workflows are strongly relational |
| Supabase/Postgres | Leading Trigger Later profile | real multi-user persistence/auth/storage/realtime is needed and a timed drill proves setup cost acceptable |
| MongoDB Atlas/time series | Evidence Needed | supplied data is high-volume, append-heavy, highly variable telemetry and planned queries/team skill favor it |
| `pgvector`/vector service | Trigger Later | semantic retrieval is part of the hero behavior and keyword/structured retrieval is insufficient |
| Next.js server/BFF | Probable default | team is proficient and challenge does not require Python-native backend work |
| FastAPI service | Trigger Later | Python ML/analytics/streaming provides material value that cannot stay in an offline job or module |
| Native `fetch` | Probable default | use Axios only for a specific interceptor/client requirement |
| One chart library | Decide from team skill | select one after a 30-minute spike; do not carry both Recharts and Chart.js |
| LLM provider interface | Lock boundary only | activate one provider plus deterministic mock when generative behavior is essential |
| LangGraph/Pinecone/RAG | Trigger Later | verified multi-step orchestration or grounded document retrieval requirement |
| Twilio/maps/PDF generation | Trigger Later | activated workflow and rubric explicitly need them |

### 11.3 Architecture views

Maintain text descriptions beside diagrams so architecture remains understandable without the drawing tool.

Required views:

1. System context.
2. Container/runtime view.
3. Component/module view.
4. Data-flow view.
5. Deployment view.
6. Trust-boundary view.
7. Golden-path sequence.
8. ElevenLabs voice-session sequence.
9. Data/analytics pipeline.
10. Failure/fallback view.

### 11.4 Integration catalog

For each external service:

- Purpose.
- Owner.
- Data sent and received.
- Authentication method.
- Rate and quota limits.
- Cost exposure.
- Timeout/retry policy.
- Privacy/security implications.
- Local mock.
- Demo fallback.
- Exit/replacement strategy.

### 11.5 API and event contracts

Plan before implementation:

- Resource naming.
- Request and response schemas.
- Error format.
- Pagination/filtering.
- Versioning.
- Authentication and authorization.
- Idempotency.
- Correlation IDs.
- Webhook signature validation.
- Async job status.
- Event names and payloads.

Use OpenAPI/JSON Schema when implementation begins, but agree on boundaries first.

### 11.6 Offline and synchronization contract

Any activated field workflow must specify local identifiers, observed and ingestion timestamps, idempotency keys, ordered replay, retry/backoff, versioning, conflict ownership, attachment queues, deletion/tombstone semantics, and a visible sync state. Offline-created records must not silently overwrite server changes. Degraded mode must favor read-only or draft behavior when data quality, authorization, or synchronization state is uncertain.

## 12. Excalidraw diagram system

### 12.1 Source-of-truth policy

- Store editable `.excalidraw` files in `docs/04-architecture/diagrams/sources/`.
- Store exported SVG and PNG files in `docs/04-architecture/diagrams/exports/`.
- Use SVG in documentation when rendering support is reliable.
- Use high-resolution transparent PNG for presentation software.
- Export PDF only for handoff or printing.
- Never make a slide-only diagram the canonical source.
- Include diagram title, version/date, owner, scope, legend, and assumptions.

### 12.2 Naming convention

```text
01-system-context.excalidraw
01-system-context.svg
02-runtime-containers.excalidraw
02-runtime-containers.svg
03-golden-path-sequence.excalidraw
03-golden-path-sequence.svg
04-voice-session-sequence.excalidraw
04-voice-session-sequence.svg
```

### 12.3 Visual conventions

- Users/roles: one consistent shape and color.
- Internal components: one palette.
- External providers: another palette with dashed boundaries.
- Persistent data stores: standard database shape.
- Trust boundaries: red or orange dashed containers.
- Optional components: dotted borders.
- Mock/fallback paths: gray dashed arrows.
- Primary demo path: thick accent arrows.
- Number sequence steps when order matters.
- Keep text readable at presentation distance.
- Avoid crossing arrows and decorative detail.

### 12.4 Diagram review checklist

- Does the title describe the view and scope?
- Is the audience clear?
- Is every acronym explained?
- Are system boundaries unambiguous?
- Are optional and external elements distinguished?
- Does the diagram match current ADRs and context?
- Is sensitive or proprietary information absent?
- Can it be understood within 20 seconds on a slide?
- Is the editable source committed with its export?

### 12.5 Diagram-to-deck variants

Create two exports where necessary:

- **Engineering version:** includes boundaries, protocols, data stores, and fallbacks.
- **Judge version:** shows user, core product, important intelligence, voice, and value flow.

The simplified version must remain truthful and derive from the canonical design.

## 13. Data and AI planning

### 13.1 Data source inventory

For every potential dataset:

- Owner/source.
- Access status.
- License and usage limits.
- Format and size.
- Time range and granularity.
- Entities and identifiers.
- Units and timezone.
- Missingness and quality.
- Sensitive fields.
- Label availability.
- Refresh/update behavior.
- Demo availability.

### 13.2 Data dictionary and canonical contracts

Define names, types, units, nullability, ranges, examples, provenance, sensitivity, and transformation rules.

The storage-neutral conceptual model should be able to represent, without requiring every table in every challenge:

- organizations, users, memberships, and role/permission assignments;
- sites and geofences;
- assets, asset identifiers, devices, and data sources;
- telemetry measurements and fault events;
- inspections, observations, and media;
- recommendations, maintenance plans, work orders, and alerts;
- notification deliveries and audit events.

Contract rules:

- Do not store an authentication token as a user field; authentication/session material belongs to the chosen identity mechanism.
- A model designation such as `CAT-336` is not a unique asset identifier. Preserve serial/fleet/source identifiers separately.
- A measurement carries observed timestamp, ingestion timestamp, value, unit, source, and quality/provenance status.
- Faults are events, not a static asset field. Preserve the original code, standard, controller/source, model context, raw description, timestamps, and source payload.
- Store latitude and longitude as separate validated fields or an appropriate spatial type; do not rely on an opaque `lat_long` string.
- Normalize for analysis while retaining immutable raw input and transformation provenance.

### 13.2.1 J1939 and severity policy

Use real SAE J1939 concepts only when the challenge or permitted dataset supports them. SPN/FMI examples may be labelled synthetic teaching fixtures, but do not claim that a given code has a universal Level 1/3/4 severity or always implies a specific machine response. Application severity depends on OEM documentation, controller, machine model, operating context, and team policy. Keep `fault code`, `source interpretation`, `application severity`, `confidence`, and `recommended response` as separate fields. Cite the authoritative data source or mark the interpretation simulated.

### 13.3 Synthetic-data plan

- Which scenarios are generated.
- Which correlations must appear.
- How randomness is seeded.
- How ground truth is separated.
- How generated data is labelled in the UI and deck.
- How fixtures are reset.
- How synthetic results must not be represented as real-world performance.

### 13.4 Analytics/model planning

- Decision or prediction being supported.
- Baseline method.
- Candidate advanced method.
- Features available at decision time.
- Train/evaluation split policy.
- Metrics and minimum acceptable performance.
- Error costs.
- Threshold selection.
- Explainability output.
- Human review.
- Monitoring/drift concept.
- Fallback when the model is absent or uncertain.

### 13.5 Model card

Include intended use, excluded uses, data, metrics, limitations, fairness/safety issues, uncertainty, human oversight, and version.

### 13.6 Proof-and-Trust Harness

Every cartridge must plan a small proof harness before any advanced model is chosen:

- deterministic fixtures with seeded scenarios and known ground truth;
- a simple rules/statistical/manual baseline;
- provenance from raw input through transformation to displayed claim;
- error and false-alert measures appropriate to the decision;
- uncertainty and insufficient-data states;
- human confirmation for consequential recommendations;
- an audit record of input, model/rule version, output, user decision, and outcome;
- offline/provider-failure behavior;
- a claims ledger that distinguishes measured prototype results, public facts, estimates, and simulations.

No “AI-powered,” “predictive,” “real-time,” or impact claim enters the demo or deck without a corresponding proof record and limitation.

## 14. Security, privacy, and responsible-use planning

### 14.1 Threat model

Identify:

- Assets: credentials, industrial data, location, user identity, transcripts, reports.
- Actors: user, admin, external provider, attacker, accidental insider.
- Entry points: upload, API, browser, voice, webhook, retrieval documents.
- Trust boundaries.
- Threats and mitigations.
- Residual risks.
- Demo-only exceptions.

### 14.2 Abuse cases

- Malicious uploaded data.
- Prompt injection in documents.
- Voice command spoofing.
- Unauthorized tool invocation.
- Duplicate webhook action.
- Secret leakage.
- Resource/credit exhaustion.
- Fabricated safety or maintenance advice.
- Data exfiltration through generated output.
- Misrepresentation of synthetic results.

### 14.3 Privacy plan

- Data minimization.
- Consent for microphone, transcript, and recording.
- Storage and retention defaults.
- Redaction.
- Deletion/reset.
- Provider data flow.
- Location and employee-data handling.
- Screenshot/demo sanitization.

### 14.4 Responsible AI plan

- Approved and prohibited decisions.
- Human confirmation points.
- Citation/evidence requirements.
- Uncertainty communication.
- Bias/fairness considerations.
- Feedback and correction.
- Model limitations.
- Safety disclaimer boundaries.

### 14.5 Competition rules and provenance gate

Before implementation, record the organizer's rules for pre-event work, reusable boilerplate, open-source and third-party services, AI assistance, data licensing, intellectual property, public disclosure, team eligibility, submission ownership, and required attribution. Maintain a provenance ledger that distinguishes pre-event reusable material from event-created work. If official rules are not yet published, the gate remains **Evidence Needed**; prepare documents and concepts, but do not assume a prebuilt application is eligible.

### 14.6 Industrial safety gate

The starter pack provides advisory decision support only unless the official challenge explicitly authorizes a controlled simulation. It must not issue commands to physical equipment. Safety- or maintenance-related output must show supporting evidence, source and freshness, uncertainty/limitations, and a clear responsible human. Consequential actions require explicit confirmation and an audit event. Poor connectivity, stale data, low quality, or failed authorization must degrade to read-only, draft, or “insufficient evidence,” never silent autonomous action.

Avoid authoritative impersonation such as “You are a Master Caterpillar Technician.” Use a bounded role such as: “You are a maintenance decision-support assistant. Summarize supplied evidence, cite sources, state uncertainty, propose safe checks, and require qualified human approval.”

### 14.7 Brand and intellectual-property policy

Do not treat `#FFCC00`, Caterpillar trade dress, logos, product names, fault interpretations, or documentation as free design assets. Use a neutral industrial visual system until an organizer-provided brand kit or written permission defines permitted use. Clearly label the prototype as an independent hackathon concept unless the event directs otherwise, and track licenses/attribution for every dataset, icon, font, voice, media asset, and code dependency.

## 15. Delivery planning

### 15.1 Work breakdown structure

Each work item needs:

- ID.
- Outcome, not vague activity.
- Owner.
- Estimate/timebox.
- Dependencies.
- Acceptance criteria.
- Verification command or evidence.
- Demo relevance.
- Risk.

### 15.2 Dependency register

Track people, decisions, credentials, datasets, services, hardware, environments, and external approvals.

### 15.3 Risk register

Recommended columns:

| Risk | Probability | Impact | Early signal | Prevention | Contingency | Owner | Status |
|---|---:|---:|---|---|---|---|---|

Cover at least:

- Unknown data quality.
- Over-scoping.
- External-service outage.
- ElevenLabs quota/network latency.
- Merge conflicts.
- Model performance failure.
- Demo environment mismatch.
- Incomplete integration.
- Privacy/rule violation.
- Missing final assets.
- Presentation overrun.
- Key team member unavailable.

### 15.4 Decision gates

Use explicit gates:

- Planning ready.
- Architecture accepted.
- First vertical slice complete.
- Feature complete.
- Demo freeze.
- Submission ready.

Each gate needs evidence and a named approver.

### 15.5 Repository and integration policy

When implementation is authorized, use protected `main` plus short-lived feature branches and frequent vertical integration. Do not create long-lived `frontend`, `backend`, and `ai_agent` branches; they defer conflicts until the most expensive moment. Confirm every teammate can authenticate to the repository before the event, but keep the initial repository private only if event rules and team policy permit it.

## 16. Test and verification planning

Define before coding:

- Unit-test boundaries.
- Contract tests.
- Integration workflows.
- Browser smoke tests.
- Accessibility checks.
- Security checks.
- Data-quality tests.
- Model evaluation.
- Voice latency and fallback tests.
- Demo reset verification.
- Manual exploratory checklist.

For every critical requirement, record how it will be proven. “It worked once” is not a verification strategy.

## 17. Observability and runbook planning

### 17.1 Observability

- Important events.
- Correlation identifiers.
- Metrics and thresholds.
- Error categories.
- Redaction rules.
- Development diagnostics.
- Demo status panel.

### 17.2 Runbooks

Plan short runbooks for:

- Clean setup.
- Environment diagnosis.
- Seed/reset demo data.
- Rotate/revoke provider key.
- ElevenLabs unavailable.
- Database unavailable.
- Failed deployment.
- Restore last known-good demo.
- Presentation laptop setup.
- Final submission packaging.

## 18. Demo planning

### 18.1 Scenario catalog

Use the three pre-event cartridges in Section 8.3 to test adaptability; do not maintain an unbounded list of speculative products. Each scenario specifies setup state, trigger, user action, data-to-action flow, expected output, proof of value, dependencies, safety boundary, and fallback. Voice-guided inspection, knowledge retrieval, parts planning, or alerts are optional behaviors within a cartridge, not separate default products.

### 18.1.1 Timed surprise drills

Before declaring the plan implementation-ready, run at least two paper/prototype-free mock hackathons:

1. one fleet/asset-uptime prompt;
2. one non-fleet prompt such as field safety, energy, workforce, or jobsite productivity;
3. make at least one drill degraded/offline or provider-unavailable.

For each drill, measure time from reveal to completed Challenge Compiler, MVP/non-goal lock, architecture activation choices, data contract, diagram/story outline, and risk/fallback plan. Record where the starter pack accelerated or constrained the team and delete/simplify components that slowed adaptation.

If activating the Supabase hosted profile consumes more than one-third of the expected build window in two representative drills, either promote more of that profile into the permitted baseline or choose a cheaper persistence path. Apply similar thresholds to voice and AI providers: an optional integration that cannot prove hero-path value inside its timebox is cut.

### 18.2 Demo script

For each step:

- Timestamp.
- Presenter.
- Spoken line.
- Exact action.
- Expected visual/audio result.
- Purpose in the narrative.
- Fallback if it fails.

### 18.3 Fallback matrix

| Dependency | Preferred path | Fallback 1 | Fallback 2 | Switch trigger | Owner |
|---|---|---|---|---|---|

Include internet, voice, model, database, map, deployment, microphone, and presentation-display failures.

### 18.4 Demo freeze

After freeze:

- Only critical fixes.
- No dependency upgrades.
- No schema redesign.
- No visual redesign outside broken presentation issues.
- Protect/tag the known-good revision.
- Record exact startup/reset commands.
- Capture backup video and screenshots.

## 19. Final presentation plan

`PRESENTATION_SYSTEM_PLAN.md` is the canonical production system for intermediate reviews and the final deck. This section only defines its integration with planning; do not duplicate templates or workflows here. Every intermediate deck should be a smaller truthful projection of the same claims ledger, architecture source, decision record, and product evidence that will feed the final deck.

### 19.1 Recommended core deck

Target approximately 8–12 core slides depending on the event rules.

1. **Title and hook** — one memorable sentence.
2. **User and problem** — show the real workflow and pain.
3. **Why it matters** — quantify operational or human impact.
4. **Solution** — one clear product view.
5. **Demo transition** — what the audience should watch for.
6. **How it works** — simplified architecture diagram.
7. **Data/intelligence** — evidence, model/rules, and explainability.
8. **Interaction advantage** — voice only if the activated use case proves it materially helps.
9. **Impact and validation** — measured results or labelled estimates.
10. **Safety, trust, and limitations** — concise credibility slide.
11. **Adoption and roadmap** — integration and scaling path.
12. **Closing** — restate outcome and ask.

### 19.2 Backup slides

- Detailed architecture.
- Data schema and lineage.
- Evaluation methodology.
- Confusion matrix/threshold tradeoff.
- Security and privacy.
- Cost assumptions.
- Failure handling.
- Competitive/alternative comparison.
- Team contributions.
- References.

### 19.3 Slide acceptance criteria

- One primary message per slide.
- Claim is backed by evidence or labelled as an estimate.
- Readable at distance.
- Minimal paragraphs.
- Consistent terminology and visual language.
- Architecture matches current system.
- Screenshots use realistic but non-sensitive data.
- Demo and deck tell the same story.
- Presenter can explain every number and component.

### 19.4 Media shot list

Plan captures for the activated cartridge, not a presumed fleet UI:

- Hero operational workspace or workflow.
- Source-to-recommendation evidence trail.
- Voice interaction with transcript, only if activated.
- Draft/confirmation workflow.
- Before-and-after or impact view.
- Architecture diagram.
- Team/product photo if appropriate.
- 20–60 second backup clips for unreliable live features.

### 19.5 Presentation production workflow

1. Lock narrative before visual polish.
2. Assign evidence and owner to each slide.
3. Build diagrams from canonical Excalidraw sources.
4. Use product screenshots after UI freeze.
5. Write speaker notes and transition lines.
6. Rehearse with a timer and interruptions.
7. Export to PPTX and PDF.
8. Test on the presentation device and offline.
9. Store a cloud and local backup.
10. Verify fonts, video, audio, links, and aspect ratio.

### 19.6 Presentation-ready evidence generated during work

Maintain these small, reusable inputs so intermediate and final decks do not require archaeology:

- **Claim card:** claim, evidence/source, confidence, limitation, owner, slide/demo usage.
- **Decision snapshot:** decision, alternatives, rationale, consequence, ADR link.
- **Metric snapshot:** definition, baseline, current value, method, sample size, timestamp.
- **Architecture change note:** what changed and which Excalidraw source/export was updated.
- **Screenshot/media manifest:** scenario, fixture version, capture owner, safe-to-share status, retake trigger.
- **Demo moment card:** setup, action, expected result, proof, fallback, and 15-second spoken explanation.

At each review checkpoint, generate a 3–5 slide status deck from these sources: problem/current hypothesis, decisions/architecture, working evidence, risks/asks, and next gate. The final deck expands the same story rather than starting over.

## 20. Team synchronization system

### 20.1 Daily or session start

Every contributor reads:

1. `CONTEXT.md`.
2. Active requirement/use-case document.
3. Relevant ADRs.
4. Assigned work item and acceptance criteria.

### 20.2 Handoff format

```markdown
## Handoff
- Objective:
- Current state:
- Files/artifacts changed:
- Decisions made:
- Verification performed:
- Known issues:
- Next exact action:
- Context/ADR updates required:
```

### 20.3 Meeting notes

Meeting notes should capture decisions, actions, owners, and deadlines. Afterward:

- Durable decisions move to ADRs.
- Current truth moves to `CONTEXT.md`.
- Tasks move to the work breakdown/backlog.
- Raw notes remain as historical input.

### 20.4 Context freshness check

Before starting a major work session, verify:

- Timestamp is current.
- Phase and scope are accurate.
- Active work ownership is correct.
- Locked decisions link to accepted ADRs.
- Risks/blockers are still active.
- Verification claims match current evidence.

## 21. Planning phases

### Phase A — Compact planning system

- Create and assign the Challenge Compiler, Lock/Trigger Register, `CONTEXT.md`, rules/provenance sheet, decision index, evidence/claims register, and risks/drills log.
- Apply an artifact budget and merge/delete duplicated planning material.
- Agree on context freshness, ADR promotion, diagram source, handoff, and presentation evidence rules.

### Phase B — Problem-agnostic preparation

- Define the reusable identity/role, operational workspace, and data-to-action concepts without implementing them.
- Define storage-neutral entities, units, timestamps, quality, provenance, offline sync, and safety policies.
- Specify no more than three scenario cartridges and deterministic fixture/ground-truth plans.
- Record technology activation triggers and provider fallbacks; do not accept problem-dependent choices early.
- Run two timed surprise drills, including a non-fleet and a degraded/offline case, then simplify the plan from evidence.

### Phase C — Rules and event intake

- Capture official prework, IP, data, AI/tool, sponsor, eligibility, submission, schedule, and judging rules.
- Record team availability, skills, machines, credentials, network assumptions, and required platforms.
- Reconcile the provenance ledger and mark every unresolved rule as a blocker or explicit risk.

### Phase D — Problem reveal and compilation

- Complete the one-page Challenge Compiler.
- Identify the user, decision/job, environment, outcome, permitted data, hero behavior, trust requirements, and measurable proof.
- Select or create a cartridge; never force the prompt into a fleet dashboard.
- Lock one hero behavior, one or two supporting behaviors, non-goals, deletion order, and activated Trigger Later items.
- Update context, risks, claims, architecture, data contracts, and presentation story.

### Phase E — Implementation planning

- Break the vertical slice into short-lived, independently verifiable work items.
- Allocate owners, integration checkpoints, timeboxes, acceptance criteria, and cut lines.
- Plan deterministic demo data, reset, provider mocks, offline behavior, and proof collection.
- Pass the implementation-readiness gate in Section 23.

### Phase F — Build and continuous evidence

Implementation begins only after the gate. Integrate vertically and frequently; update evidence, claims, context, ADRs, risks, diagrams, screenshot manifests, and intermediate presentation inputs as facts change.

### Phase G — Demo freeze and presentation

- Freeze implementation and protect the known-good revision.
- Capture safe media and the backup demo.
- Reconcile every deck claim with evidence and limitations.
- Finalize canonical diagrams, deck, PDF, speaker notes, Q&A, fallbacks, and submission package.

## 22. Lock / Trigger / Evidence / Merge / Delete register

The live version belongs in `planning/lock-trigger-register.md`. This is the council-approved starting state.

### 22.1 Lock Now

- Compact artifact system, ownership/freshness rules, ADR promotion rule, and traceable claim/evidence process.
- Challenge Compiler and maximum-three-cartridge discipline.
- Storage-neutral domain and provider boundaries.
- Deterministic fixtures/replay, synthetic-data labels, ground truth, and demo reset.
- Units, dual timestamps, source, quality, raw-input retention, and provenance policies.
- Human confirmation, advisory-only safety, audit events, secrets policy, and no browser-exposed provider credentials.
- Offline/degraded contract and visible sync/quality state.
- Neutral industrial design; canonical Excalidraw source plus judge/engineering exports.
- Protected `main`, short-lived feature branches, frequent integration, and provider mocks/fallbacks.
- ElevenLabs is optional behind an adapter with text/touch equivalence.

### 22.2 Trigger Later

- Real login/authentication and finalized roles.
- Supabase/Postgres hosted profile, deployment target, object storage, and realtime.
- Separate Python/FastAPI analytics service.
- ElevenLabs speech or conversational agent.
- LLM, RAG, pgvector/vector database, LangGraph, and external knowledge ingestion.
- MongoDB/time-series database, maps/geospatial provider, Twilio/notifications, and PDF generation.
- Specific dashboard, KPI, machine/fleet workflow, report format, and enterprise integration.

### 22.3 Evidence Needed

- Official competition rules and permitted pre-event work.
- Supplied datasets, interfaces, licenses, schema, size, quality, labels, and update pattern.
- Judging rubric, presentation duration, submission format, network/device constraints, and sponsor requirements.
- Team stack proficiency and timed activation cost for hosted database, AI, and voice.
- Authoritative fault-code interpretation, severity policy, unit conventions, and domain-expert validation.
- Permission to use Caterpillar branding, product marks, screenshots, documentation, or branded color treatment.

### 22.4 Merge

- Presentation detail belongs in `PRESENTATION_SYSTEM_PLAN.md`; this file holds only integration gates.
- Current truth belongs in `CONTEXT.md`; this file holds durable planning policy.
- Broad capability ideas remain in `HACKATHON_STARTER_PACK_PLAN.md`, but activated scope and decisions live here and in the registers.
- Initial assumptions, questions, risks, dependencies, and compact ADRs may share registers until volume justifies separate artifacts.

### 22.5 Delete or reject as defaults

- Long-lived frontend/backend/AI branches.
- Mandatory fleet dashboard, mandatory login, or mandatory AI/voice.
- Multiple LLM/STT providers, two chart libraries, broad CORS, or Axios without a demonstrated need.
- Prebuilt RAG/LangGraph/Pinecone/Twilio/maps/report-generation stacks.
- Universal J1939 severity mapping or unqualified OEM fault interpretation.
- “Master Caterpillar Technician” impersonation and autonomous safety/maintenance action.
- Unauthorized Caterpillar trade dress or an unverified “official” color code.
- Empty documents, duplicate plans, and integrations without owner, trigger, proof, fallback, and cut condition.

## 23. Implementation-readiness gate

Implementation may begin only when the applicable gate is satisfied. Before a problem reveal, “implementation-ready” means the planning system has survived drills; it does not authorize building the application.

### 23.1 Pre-event planning gate

- [ ] Challenge Compiler and Lock/Trigger Register are usable and owned.
- [ ] Artifact budget has removed or merged unmaintainable documents.
- [ ] Three-or-fewer cartridges, storage-neutral contracts, deterministic fixtures, offline policy, safety policy, and proof harness are specified.
- [ ] Two timed surprise drills passed, including one non-fleet and one degraded/offline case; lessons changed the plan.
- [ ] Hosted database, voice, and AI activation time/cut thresholds are recorded.
- [ ] Competition-rule questions and pre-event provenance are recorded without assuming eligibility.
- [ ] Presentation evidence/diagram system can produce a truthful intermediate review.

### 23.2 Post-reveal build authorization gate

- [ ] Official rules, rubric, constraints, permitted tools/data, and submission requirements are captured.
- [ ] Challenge Compiler is complete and approved by the team.
- [ ] One hero behavior, at most two supporting behaviors, measurable outcome, explicit non-goals, and deletion order are locked.
- [ ] Activated technologies satisfy their evidence triggers; rejected technologies are recorded.
- [ ] Data contracts cover identifiers, units, timestamps, source, quality, provenance, licensing, and raw retention.
- [ ] Safety, privacy, authorization, confirmation, audit, offline/degraded, and provider-failure behavior are explicit.
- [ ] Vertical work items have owners, timeboxes, dependencies, acceptance criteria, integration points, and verification evidence.
- [ ] External dependencies have deterministic mocks/fallbacks and a known-good reset path.
- [ ] System context, golden-path, trust/data-flow, and failure diagrams are scoped; unnecessary views are deferred.
- [ ] Claims ledger, presentation story, demo moments, media plan, and fallback owner align with the MVP.

## 24. Planning deliverables checklist

### Must have before implementation

- Current `CONTEXT.md` with owner and freshness timestamp.
- Completed Challenge Compiler and Lock/Trigger Register.
- Rules/provenance sheet and team ownership/handoff agreement.
- Compact decisions/ADR index with activation evidence.
- MVP/non-goals, requirements, acceptance criteria, and cut order.
- Activated architecture/data/safety/offline/provider decisions and deterministic fixture plan.
- Proof-and-Trust Harness, risk/drill results, work breakdown, demo/reset/fallback plan.
- Presentation story, claims/evidence register, diagram inventory, and media plan.

Create `README.md`, `AGENTS.md`, separate threat model, detailed test strategy, full data dictionary, provider-specific voice plan, and other catalog artifacts only when the revealed challenge or implementation scale activates them.

### Must have before final submission

- Current context and architecture.
- Complete traceability for judged requirements.
- Updated ADRs.
- Data/model evidence and limitations.
- Security/privacy summary.
- Verified demo script and fallbacks.
- Final Excalidraw sources and exports.
- Presentation deck and PDF.
- Speaker notes.
- Backup screenshots/video.
- Submission checklist and verified package.

## 25. Recommended next planning sequence

1. Approve this council redline as the governing plan; do not implement application code.
2. Create the one-page Challenge Compiler and Lock/Trigger Register.
3. Inventory every proposed document/integration against owner, decision, budget, trigger, fallback, and delete/merge rule.
4. Consolidate duplicate content across the three planning files and create the initial `CONTEXT.md`.
5. Obtain official competition rules when available; record team constraints and pre-event provenance now.
6. Define the storage-neutral data, provenance, offline, safety, and proof contracts.
7. Bound the three scenario cartridges and their seeded fixture/ground-truth specifications.
8. Define the Supabase/Postgres, MongoDB, FastAPI, AI/RAG, ElevenLabs, maps, alerts, and report activation tests and timeboxes.
9. Run the fleet-focused timed surprise drill; record time, failure points, and plan changes.
10. Run the non-fleet degraded/offline drill; record time, failure points, and plan changes.
11. Delete or simplify preparation that did not accelerate either drill.
12. Confirm the presentation evidence pipeline can produce a 3–5 slide intermediate review and canonical Excalidraw exports.
13. Review the pre-event gate. Stop at planning readiness until the actual rules and problem statement arrive.
14. At reveal, run the Challenge Compiler, activate only evidenced options, and pass the post-reveal gate.
15. Only then convert the approved vertical slice into implementation work.

## 26. What to avoid during planning

- Writing dozens of unowned documents.
- Treating tool/framework selection as product strategy.
- Choosing architecture before ranking quality attributes.
- Using “AI-powered” or “real-time” without defining behavior and evidence.
- Designing voice without a real user constraint.
- Mixing raw research, decisions, current context, and tasks in one file.
- Building presentation diagrams independently from architecture sources.
- Claiming production readiness from a hackathon prototype.
- Letting the deck promise features the demo cannot show.
- Beginning implementation because planning feels slow while critical scope or integration questions remain unresolved.
- Anchoring on login/dashboard/analytics and then rewriting the problem to fit the prepared UI.
- Treating Caterpillar's connected-machine products or a prior hackathon as proof of the next theme.
- Protecting elaborate pre-event plans because the team invested effort in them; drills are allowed to delete work.
- Underestimating integration, verification, rehearsal, and fallback time while overvaluing feature count.
- Building a persuasive “Caterpillar means telematics” narrative from selectively confirming evidence.
