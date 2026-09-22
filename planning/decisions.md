# Architecture Decision Records (ADRs)

> **Status:** Live active ADR index (Epic E-00 baseline).  
> **Governing Council Review:** `council-report-20260921-122900Z-qc00bdca0.html` (Verdict SHA: `c00bdca0`).

---

## ADR Index

- [ADR-0001: Adopt Modular Industrial Spine Architecture](#adr-0001-adopt-modular-industrial-spine-architecture)
- [ADR-0002: Storage-Neutral Domain Contracts with Deterministic Local Fixtures](#adr-0002-storage-neutral-domain-contracts-with-deterministic-local-fixtures)
- [ADR-0003: Strict Advisory Decision Support and Human Confirmation Boundary](#adr-0003-strict-advisory-decision-support-and-human-confirmation-boundary)
- [ADR-0004: Neutral Industrial Design System and Absence of Caterpillar Trade Dress](#adr-0004-neutral-industrial-design-system-and-absence-of-caterpillar-trade-dress)
- [ADR-0005: Pinned Core Technology Stack](#adr-0005-pinned-core-technology-stack)
- [ADR-0006: Separate Reusable Core from Challenge Cartridges](#adr-0006-separate-reusable-core-from-challenge-cartridges)

---

## ADR-0001: Adopt Modular Industrial Spine Architecture

- **Status:** Accepted
- **Date:** 2026-09-22
- **Context:** The hackathon challenge requires high operational agility. Building a monolithic, hardcoded fleet management tool risks immediate obsolescence if the challenge centers on workforce safety, dealer operations, or fluid analysis.
- **Decision:** Build a bounded modular industrial spine (capture trustworthy evidence -> establish context & quality -> evaluate deterministic rules -> recommend safe action -> require human confirmation -> record audit log).
- **Consequences:** Highly adaptable; zero dead code; low integration risk; clean separation between domain logic, UI, and external providers.

---

## ADR-0002: Storage-Neutral Domain Contracts with Deterministic Local Fixtures

- **Status:** Accepted
- **Date:** 2026-09-22
- **Context:** Relying on hosted databases (Supabase, Postgres, MongoDB) introduces network latency, migration overhead, connection leaks, and quota/availability failure points during judging demos.
- **Decision:** Define storage-neutral repository interfaces (`AssetRepository`, `TelemetryRepository`, `WorkOrderRepository`, `AuditRepository`) backed by a deterministic in-memory/JSON baseline fixture loader. External databases remain Trigger Later behind adapters.
- **Consequences:** Guaranteed 100% reproducible tests and instant demo reset. No network dependency during presentation.

---

## ADR-0003: Strict Advisory Decision Support and Human Confirmation Boundary

- **Status:** Accepted
- **Date:** 2026-09-22
- **Context:** Industrial heavy machinery operates in hazardous environments. Autonomous software commanding physical actuators or engine shutdowns is unsafe, legally hazardous, and forbidden by competition rules.
- **Decision:** The product is strictly decision support. All system outputs are advisory recommendations carrying confidence levels and evidence citations. Any consequential action (dispatching service, changing machine status) requires explicit human confirmation and creates an immutable audit record.
- **Consequences:** Satisfies industrial safety standards, builds user trust, and adheres strictly to competition guidelines.

---

## ADR-0004: Neutral Industrial Design System and Absence of Caterpillar Trade Dress

- **Status:** Accepted
- **Date:** 2026-09-22
- **Context:** Using official Caterpillar logos, trademarked trade dress, or unverified paint color hex codes without formal written organizer permission creates legal, IP, and credibility risks.
- **Decision:** Implement a clean, modern, neutral industrial theme ("Equipment Operations Workspace") using charcoal, slate, steel gray, and high-visibility alert accents (amber/emerald/crimson). No trademarked logos or official Cat brand kits are used.
- **Consequences:** Protects team against IP disqualification; ensures high readability in variable lighting environments.

---

## ADR-0005: Pinned Core Technology Stack

- **Status:** Accepted
- **Date:** 2026-09-22
- **Context:** Preflight requires explicit, pinned stack choices. Silently choosing tools or swapping dependencies during implementation causes DAG failures and integration churn.
- **Decision:** Pin the stack to:
  - **Runtime:** Node.js LTS (>= 20.x)
  - **Package Manager:** npm (>= 10.x)
  - **Framework:** Next.js 14 (App Router) + TypeScript
  - **Styling:** Vanilla CSS / CSS Modules with responsive tokens
  - **Charts:** Recharts (single chart library)
  - **Testing:** Vitest
  - **Code Quality:** ESLint, Prettier, TypeScript `tsc`
- **Consequences:** Unified full-stack TypeScript environment; single dev server; zero microservice sprawl; fast CI/local test feedback.

---

## ADR-0006: Separate Reusable Core from Challenge Cartridges

- **Status:** Accepted
- **Date:** 2026-09-22
- **Context:** The reference implementation placed fleet, asset, telemetry, coolant, J1939, work-order, safety, offline, and evidence concepts under one generic `src/domain` namespace. That made a single mock cartridge appear universal and increased the risk of forcing an unrelated revealed problem into fleet terminology.
- **Decision:** Keep challenge-neutral evidence, deterministic runtime, consequential-action safety, and offline queue contracts in `src/core`. Keep the asset-maintenance implementation in `src/cartridges/asset-maintenance`. Preserve its mock planning, QA, review, diagram, and presentation artifacts under `examples/asset-maintenance`. Live unresolved reveal documents remain under `planning`.
- **Consequences:** A new challenge can reuse the core without importing fleet concepts; the maintenance demo remains executable; historical evidence is clearly separated from current truth. Imports and documentation must respect the boundary, and any new cartridge owns its domain types, fixtures, rules, UI, adapters, and cartridge-specific tests.
- **Validation:** `tests/core/reusable-core.test.ts` exercises the core with a non-fleet hazard example, while all fleet tests import through the asset-maintenance cartridge.
- **Revisit trigger:** A repeated pattern proven across at least two distinct cartridges may be promoted into `src/core`; speculative abstractions must remain cartridge-local.
