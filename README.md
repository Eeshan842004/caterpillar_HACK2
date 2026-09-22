# Caterpillar Hackathon Starter Pack

> **Status:** Verified pre-event starter with a challenge-neutral core and an isolated
> asset-maintenance reference cartridge.
>
> **Important:** The official problem statement, judging rubric and reusable-code ruling have
> not been recorded. The included application is a mock adaptation drill, not an official
> Caterpillar submission.

This repository is designed to shorten the time between receiving an unknown problem statement
and demonstrating one credible, evidence-backed solution. It supplies planning gates, reusable
technical contracts, tested tooling, a worked industrial example and a presentation workflow.

It does **not** assume that every challenge needs authentication, a fleet dashboard, a database,
AI or voice. Those capabilities are activated only when the revealed problem earns them.

## Start here

| Need                                                              | Read or edit                                                                                                                            |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Understand what can be reused and what happens after the reveal   | [Starter Pack Guide](STARTER_PACK_GUIDE.md)                                                                                             |
| See the current repository state and active handoff               | [Current Context](CONTEXT.md)                                                                                                           |
| Understand the council-reviewed planning strategy                 | [Planning A-to-Z](PLANNING_A_TO_Z.md)                                                                                                   |
| Fill in the revealed problem                                      | [Live Challenge Compiler](planning/challenge-compiler.md)                                                                               |
| Record the exact build after scope is approved                    | [Live Implementation Manifest](planning/implementation-manifest.md)                                                                     |
| Verify rules, sources and prework eligibility                     | [Rules and Provenance Register](planning/rules-and-provenance.md)                                                                       |
| Decide whether a capability should be activated                   | [Lock / Trigger Register](planning/lock-trigger-register.md)                                                                            |
| Review architecture decisions                                     | [Architecture Decision Records](planning/decisions.md)                                                                                  |
| Plan intermediate and final presentations                         | [Presentation System Plan](PRESENTATION_SYSTEM_PLAN.md)                                                                                 |
| Coordinate implementation with Gemini agents                      | [Gemini Coordinator Prompt](GEMINI_COORDINATOR_PROMPT.md) and [Implementation Specification](GEMINI_MULTI_AGENT_IMPLEMENTATION_SPEC.md) |
| Inspect the worked reference without treating it as current truth | [Asset-Maintenance Example](examples/asset-maintenance/README.md)                                                                       |

If you only read one document before the event, read the
[Starter Pack Guide](STARTER_PACK_GUIDE.md). It contains the reuse boundary, reveal-day gates,
optional capability criteria and ElevenLabs workflow.

## Make the repository usable now

### 1. Install and verify the baseline

Prerequisites:

- Node.js 20 or another version permitted by the event;
- npm 10 or a compatible version;
- Git configured for the team repository.

From the repository root:

```powershell
npm ci
Copy-Item .env.example .env.local
npm test
npm run type-check
npm run lint
npm run build
```

The local baseline requires no external services or paid API keys. The configuration template
is [.env.example](.env.example).

The project is currently Next.js/TypeScript. [requirements.txt](requirements.txt) is intentionally
dependency-free and becomes relevant only if the approved manifest activates Python.

### 2. Run the worked reference

```powershell
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The page demonstrates the existing
asset-maintenance cartridge, including telemetry, evidence-backed recommendations, human
confirmation, audit records, offline queue behavior and deterministic reset.

Treat this as a known-good engineering example. Do not treat its user, data, terminology,
thresholds, claims or screens as requirements for the actual challenge.

### 3. Give every teammate the same starting context

Before the event, each teammate should:

1. run the verification commands above;
2. read the [Starter Pack Guide](STARTER_PACK_GUIDE.md);
3. understand the source-of-truth order below;
4. know which live planning file they own after the reveal;
5. verify that they can create a branch, push and open a pull request;
6. avoid adding provider credentials or speculative features.

Use [CONTEXT.md](CONTEXT.md) for short-lived status and handoffs. Use
[planning/decisions.md](planning/decisions.md) for durable architecture decisions.

## Source-of-truth order

When documents disagree, use this order:

1. official event rules, problem statement and judging rubric;
2. sourced decisions in [Rules and Provenance](planning/rules-and-provenance.md);
3. the approved [Challenge Compiler](planning/challenge-compiler.md);
4. accepted [ADRs](planning/decisions.md);
5. the approved [Implementation Manifest](planning/implementation-manifest.md);
6. current code contracts and tests;
7. worked examples and archived evidence.

The files under `examples/asset-maintenance/` are historical reference material. They never
override live planning files.

## Repository boundary

```text
planning/                           live reveal documents and durable decisions
src/core/                           challenge-neutral reusable contracts
src/cartridges/asset-maintenance/   replaceable worked implementation
examples/asset-maintenance/         archived mock plans, QA, evidence and presentation
tests/core/                         proof that the core works without fleet terminology
tests/cartridges/asset-maintenance/ reference-cartridge verification
```

The public technical boundaries are:

- [challenge-neutral core](src/core/index.ts): evidence, deterministic runtime helpers,
  consequential-action policy and offline action queue;
- [asset-maintenance cartridge](src/cartridges/asset-maintenance/index.ts): fleet fixtures,
  telemetry, faults, recommendations, work orders, UI and adapters;
- [non-fleet adaptation drill](planning/drills/non-fleet-safety-observation.md): proof that the
  reusable core does not depend on asset-maintenance terminology.

## What to do when the problem statement arrives

Do these gates in order. Do not begin broad implementation while a hard gate is unresolved.

### Gate 0 — Capture authority

Record the exact problem statement, official rules, rubric, deadline, presentation format,
provided datasets/APIs and prework restrictions in
[planning/rules-and-provenance.md](planning/rules-and-provenance.md).

### Gate 1 — Compile the challenge

Complete [planning/challenge-compiler.md](planning/challenge-compiler.md) with:

- one primary user;
- one operational job or decision;
- one measurable target outcome;
- permitted inputs and constraints;
- one hero behavior and at most two supporting behaviors;
- trust, safety, non-goals and cut order.

Do not choose technologies merely because they are already present in the repository.

### Gate 2 — Select or create a cartridge

- **Strong domain match:** adapt `src/cartridges/asset-maintenance/`.
- **Partial match:** reuse only fitting components and replace domain-specific rules and names.
- **No match:** leave the reference intact and create `src/cartridges/<challenge-name>/`.

Never rename an unrelated entity “asset” simply to preserve prepared code.

### Gate 3 — Approve the build contract

Complete [planning/implementation-manifest.md](planning/implementation-manifest.md). Resolve the
stack, entities, units, fixtures, interfaces, active providers, epic DAG, ownership, QA,
fallbacks and presentation outputs.

Every optional capability remains disabled until the manifest records its owner, measurable
value, timebox, cost/quota, failure mode, fallback and cut condition.

### Gate 4 — Freeze shared contracts

Before parallel implementation, freeze:

- domain types and invariants;
- API or event contracts;
- fixture schema and ground truth;
- repository/provider interfaces;
- evidence and recommendation schema;
- confirmation and audit behavior;
- file ownership and integration checkpoints.

Use the [Gemini Coordinator Prompt](GEMINI_COORDINATOR_PROMPT.md) only after these contracts and
work items are concrete enough to delegate safely.

### Gate 5 — Build one complete vertical slice

Build this before adding optional features:

```text
permitted input
  -> validation and data quality
  -> baseline analysis
  -> evidence-backed output
  -> human review or confirmation
  -> recorded outcome
  -> resettable demonstration
```

The UI and API must use the same application path. Tests, evidence, screenshots and presentation
claims should be captured while the slice is being built—not reconstructed at the end.

## Capability activation guide

| Capability        | Activate only when                                                        | Keep as fallback                            |
| ----------------- | ------------------------------------------------------------------------- | ------------------------------------------- |
| Authentication    | identity, roles, tenants or collaboration affect the judged workflow      | deterministic demo personas                 |
| Supabase/Postgres | durable multi-user data, auth, storage or realtime is needed              | local repository and fixtures               |
| Python/FastAPI    | Python-native analytics or ML materially improves the hero behavior       | TypeScript baseline or offline job          |
| Product LLM/RAG   | generative or semantic reasoning is essential and can be evaluated        | deterministic rules or structured retrieval |
| ElevenLabs voice  | hands/eyes-busy, accessibility, language or narration value is measurable | complete text/touch workflow                |
| Maps              | location changes the decision or outcome                                  | list/table and site metadata                |
| Notifications     | external delivery is part of the required outcome                         | in-app alerts                               |
| PDF/reporting     | formal handoff or compliance output is required                           | print-ready screen                          |

For the complete activation policy, use the
[Lock / Trigger Register](planning/lock-trigger-register.md). For voice-specific design,
fallback and test requirements, see the
[ElevenLabs section of the Starter Pack Guide](STARTER_PACK_GUIDE.md#7-elevenlabs-reveal-workflow).

## Documentation map

### Live documents — edit these after the reveal

- [Challenge Compiler](planning/challenge-compiler.md) — problem, user, outcome and scope.
- [Rules and Provenance](planning/rules-and-provenance.md) — authoritative sources and reuse
  eligibility.
- [Implementation Manifest](planning/implementation-manifest.md) — exact build contract.
- [Lock / Trigger Register](planning/lock-trigger-register.md) — capability decisions.
- [Architecture Decision Records](planning/decisions.md) — durable technical decisions.
- [Current Context](CONTEXT.md) — status, ownership, blockers and handoffs.

### Planning and operating guidance

- [Starter Pack Guide](STARTER_PACK_GUIDE.md) — repository boundary and reveal-day runbook.
- [Planning A-to-Z](PLANNING_A_TO_Z.md) — council-reviewed governance and architecture strategy.
- [Presentation System Plan](PRESENTATION_SYSTEM_PLAN.md) — evidence, diagrams, decks, demo and
  rehearsal.
- [Industrial Starter Master Plan](HACKATHON_STARTER_PACK_PLAN.md) — broad capability catalog;
  useful for ideas, but not a live implementation manifest.

### Multi-agent implementation

- [Gemini Multi-Agent Implementation Specification](GEMINI_MULTI_AGENT_IMPLEMENTATION_SPEC.md) —
  detailed implementation protocol and quality bar.
- [Gemini Coordinator Prompt](GEMINI_COORDINATOR_PROMPT.md) — copy-ready coordinator prompt.

### Worked example — reference only

- [Asset-Maintenance Cartridge Overview](examples/asset-maintenance/README.md).
- [Example Challenge Compiler](examples/asset-maintenance/planning/challenge-compiler.md).
- [Example Implementation Manifest](examples/asset-maintenance/planning/implementation-manifest.md).
- [Example QA Scoreboard](examples/asset-maintenance/planning/evidence/final-scoreboard.md).
- [Example Presentation Story Arc](examples/asset-maintenance/presentation/10-presentation/story-arc.md).
- [Example Demo Script](examples/asset-maintenance/presentation/10-presentation/demo-script.md).
- [Example Evidence Register](examples/asset-maintenance/presentation/10-presentation/evidence-register.md).
- [Example Fallback Matrix](examples/asset-maintenance/presentation/10-presentation/fallback-matrix.md).

## Current verification commands

Run these before merging changes or declaring a known-good demo:

```powershell
npm test
npm run type-check
npm run lint
npm run build
```

The current starter has automated core, cartridge, API-client, route-handler and component
coverage. It does not yet include a running-browser end-to-end suite or load test.

## Safety, secrets and claims

- Do not commit `.env`, `.env.local`, provider keys or credentials.
- Keep third-party keys server-side and provide a degraded local path.
- Do not use this prototype to control physical machinery.
- Require an identified human approver for consequential actions.
- Do not claim Caterpillar endorsement, production readiness, customer savings, predictive
  accuracy, immutable storage or submission status without current evidence and permission.
- Label synthetic data, mock users and estimated outcomes clearly.

The goal is not to arrive with a prebuilt answer. The goal is to arrive with a reliable way to
turn the actual problem into a focused, testable and presentable solution.
