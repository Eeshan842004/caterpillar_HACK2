# Caterpillar Hackathon Starter Pack

> **Status:** Pre-event starter foundation with an isolated asset-maintenance reference cartridge.
>
> **Important:** No official problem statement, judging rubric, or reusable-code ruling is
> recorded yet. The reference application is a mock drill, not a submission.

## Purpose

This repository reduces hackathon setup and decision time without assuming that the real
challenge will be fleet maintenance. It provides:

- live reveal templates and implementation gates;
- a challenge-neutral evidence, determinism, safety, and offline core;
- tested TypeScript/Next.js engineering tooling;
- an asset-maintenance example showing how a cartridge can use the core;
- QA, review, demo, diagram, and presentation patterns;
- a Gemini multi-agent implementation contract.

Read `STARTER_PACK_GUIDE.md` first. It explains exactly what is reusable and what to do
when the problem statement arrives.

## Repository boundary

```text
planning/                         live challenge/rules/manifest templates
src/core/                         challenge-neutral reusable contracts
src/cartridges/asset-maintenance/ replaceable reference cartridge
examples/asset-maintenance/       archived mock plans, evidence and presentation
tests/core/                       reusable-core verification
tests/cartridges/asset-maintenance/ reference-cartridge verification
```

The live files under `planning/` intentionally contain unresolved hard blocks. The filled
asset-maintenance planning documents are examples under `examples/` and must not be copied
into the live challenge without evidence.

## Reusable technical core

- Evidence citations, data-quality states and audit-record contracts.
- Injectable clock and ID providers for repeatable tests and fixtures.
- Generic human-confirmation policy for consequential actions.
- Generic in-memory offline action queue.
- Modular-monolith and provider-adapter conventions.
- Vitest, TypeScript, ESLint, Prettier and Next.js build foundation.

## Asset-maintenance reference

The reference cartridge demonstrates:

- fleet and asset fixtures;
- telemetry/fault quality handling;
- rule-based coolant and oil-pressure recommendations;
- human-confirmed maintenance work orders;
- local offline queue and audit-hash utilities;
- a resettable UI and route-handler API examples.

It is intentionally domain-specific. Its challenge statement, rubric, user, claims and
presentation artifacts are synthetic examples.

## Local verification

Prerequisites:

- Node.js 20 or a compatible version permitted by the event.
- npm 10 or a compatible version permitted by the event.

From the repository root:

```powershell
npm install
npm test
npm run type-check
npm run lint
npm run build
npm run dev
```

Open `http://localhost:3000` to view the asset-maintenance reference cartridge.

## Problem-reveal workflow

1. Verify official rules and prework eligibility in `planning/rules-and-provenance.md`.
2. Complete `planning/challenge-compiler.md`.
3. Select the reference cartridge only if it actually fits; otherwise create a new cartridge.
4. Complete `planning/implementation-manifest.md` with exact stack/data/capability decisions.
5. Freeze domain, API/event, fixture, safety and evidence contracts.
6. Build one source-to-outcome vertical slice.
7. Activate authentication, hosted storage, AI, ElevenLabs or other providers only when
   challenge evidence justifies them.
8. Capture tests, claims, screenshots, diagrams and fallback evidence continuously.

## Optional capabilities

Disabled until activated in the live manifest:

- real authentication;
- Supabase/Postgres or MongoDB;
- FastAPI/Python analytics;
- product LLM/RAG/vector search;
- ElevenLabs voice;
- maps, notifications, PDF generation and object storage;
- realtime subscriptions and hosted deployment.

Every activation needs an owner, timebox, measurable value, fallback and cut condition.

## Known reference limitations

- The default UI consumes the API-backed state path, but automated coverage is split between
  component/client tests and route-handler integration tests; there is no running-browser E2E
  suite yet.
- Offline queue state does not survive a page refresh.
- Hashing is a tamper-detection utility, not an immutable external ledger.
- Running-server HTTP performance has not been load tested.
- No external provider, real user identity or production data is active.
- Operational and financial values are synthetic.

## Key documents

- `STARTER_PACK_GUIDE.md` — reusable boundary and reveal-day runbook.
- `PLANNING_A_TO_Z.md` — durable planning and readiness policy.
- `PRESENTATION_SYSTEM_PLAN.md` — evidence-to-deck and rehearsal system.
- `GEMINI_MULTI_AGENT_IMPLEMENTATION_SPEC.md` — implementation contract.
- `GEMINI_COORDINATOR_PROMPT.md` — copy-ready coordinator prompt.
- `planning/lock-trigger-register.md` — capability activation policy.
- `planning/decisions.md` — current durable ADRs.
- `planning/drills/non-fleet-safety-observation.md` — non-fleet adaptation proof.

## Safety and claims

This starter is advisory software only. It must not control physical machinery. Any
consequential action requires an identified human approver and an audit record.

Do not claim Caterpillar endorsement, official branding, production readiness, customer
savings, predictive accuracy, immutable storage, or event submission status without current
evidence and permission.
