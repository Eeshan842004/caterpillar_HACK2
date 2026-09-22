# Lock / Trigger / Evidence / Merge / Delete Register

> **Status:** Live active register (Epic E-00 baseline).  
> **Source:** `PLANNING_A_TO_Z.md` Section 22, governed by Council Decision `c00bdca0`.

---

## 1. Lock Now

Stable, low-cost foundations locked for implementation across all likely challenges:

- **Compact artifact system:** Single source of truth per subject, explicit ownership, freshness rules, ADR promotion criteria, and traceable claims ledger.
- **Challenge Compiler discipline:** One-page reveal-to-scope sheet, single hero behavior, maximum two supporting behaviors, and explicit non-goals.
- **Storage-neutral architecture:** Domain entities and repository interfaces decoupled from persistence implementations.
- **Deterministic local fixtures & ground truth:** Repeatable synthetic scenarios, known baseline ground truth, and an instant demo reset mechanism.
- **Data integrity rules:** Dual timestamps (UTC `observed_at` and `ingested_at`), explicit physical units (ISO standards), data quality states (`GOOD`, `SUSPECT`, `STALE`, `MISSING`, `OUT_OF_RANGE`), and raw-input retention.
- **Safety & trust boundaries:** Advisory decision support only. Never execute physical equipment control. Mandatory explicit human confirmation and immutable audit event for any consequential recommendation.
- **Offline & degraded modes:** First-class offline draft state, visible sync status, and graceful degradation on stale or missing sensor feeds.
- **Brand protection:** Neutral industrial UI theme; no Caterpillar logos, trade dress, or unverified official color codes without express permission.
- **Branch & version control:** Protected `main`, short-lived branches named `gemini/{epic-id}-{short-name}`, and deterministic mock fallbacks for all external integrations.
- **Core/cartridge boundary:** `src/core` contains only patterns proven challenge-neutral; domain entities, rules, fixtures, UI and adapters remain under a selected cartridge. Mock challenge artifacts belong under `examples`, never in live planning truth.

---

## 2. Trigger Later

Capabilities prepared conceptually, but strictly disabled until formal trigger criteria are met:

| Capability | Activation Trigger Condition | Fallback / Baseline if Not Triggered | Owner |
|---|---|---|---|
| **Real Authentication** | Multi-tenant challenge requirement or judged user collaboration requirement | Hardcoded deterministic demo personas | Lead Architect |
| **Supabase / Postgres** | Relational dataset exceeding local in-memory limits or hosted multi-user need | Local in-memory / JSON / SQLite storage-neutral repository | Data Lead |
| **MongoDB / Time-Series** | Demonstrably high-volume, schema-variable raw telemetry stream | Local structured time-series event fixtures | Data Lead |
| **Python / FastAPI Service** | Heavy numerical, predictive, or ML models requiring Python ecosystem | TypeScript domain logic and rule-based evaluation | Analytics Lead |
| **ElevenLabs Voice** | Hands-busy field technician scenario where touch/keyboard is impractical | Text/touch accessible web UI | UX Lead |
| **Product LLM / RAG** | Unstructured equipment manuals or dynamic natural language synthesis needed | Deterministic heuristic rules engine & static citation links | AI Lead |
| **pgvector / Vector Search** | Semantic retrieval over large unstructured corpus | Keyword / tag-based structured search | Data Lead |
| **Mapping / Geospatial** | Spatial fleet routing or GIS boundary judging criteria | Tabular site / asset location metadata | Frontend Lead |
| **Notifications / SMS** | Critical emergency worker safety evacuation prompt | In-app notification center | Backend Lead |
| **PDF Report Generation** | Formal executive handover or compliance reporting requirement | Clean browser print stylesheet | Frontend Lead |
| **Realtime Subscriptions** | High-frequency live streaming telemetry required during live judge demo | Polling / manual refresh with simulated replay interval | Backend Lead |

---

## 3. Evidence Needed

Active open questions requiring external verification or organizer ruling:

1. **Official Competition Rules:** Permitted pre-event code, external API rules, submission format, and deadlines.
2. **Supplied Datasets & Interfaces:** Schema, size, quality, update frequency, licensing, and format (e.g. ISO 15143-3 / AEMP 2.0).
3. **Judging Rubric & Presentation Constraints:** Scoring weights, live pitch duration, and technical Q&A format.
4. **Branding Permission:** Documented permission for Caterpillar marks, screenshots, or official trade dress (assumed NOT permitted).

---

## 4. Merge

- Detailed presentation instructions belong in `PRESENTATION_SYSTEM_PLAN.md`.
- Durable governance policy belongs in `PLANNING_A_TO_Z.md`.
- Live active status and handoffs belong in `CONTEXT.md`.
- Capability ideas remain in `HACKATHON_STARTER_PACK_PLAN.md`, but are non-binding.

---

## 5. Delete or Reject as Defaults

The following anti-patterns are explicitly prohibited:

- Long-lived frontend, backend, or AI branches.
- Mandatory login, mandatory fleet dashboard, or mandatory voice interface.
- Prebuilt RAG / LangGraph / Pinecone / Twilio / map stacks without trigger evidence.
- Universal J1939 fault severity mapping without context.
- "Master Caterpillar Technician" impersonation or autonomous equipment control.
- Unauthorized Caterpillar logos, trade dress, or unverified color codes.
