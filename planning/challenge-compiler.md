# Challenge Compiler — Reveal-to-Scope Decision Sheet

> **Status:** Approved Baseline (Epic E-00 Freeze).  
> **Source:** [`GEMINI_MULTI_AGENT_IMPLEMENTATION_SPEC.md`](file:///c:/Users/kriss/github/caterpillar-hack/caterpillar-hack/GEMINI_MULTI_AGENT_IMPLEMENTATION_SPEC.md#L65-L100) Section 4 and [`PLANNING_A_TO_Z.md`](file:///c:/Users/kriss/github/caterpillar-hack/caterpillar-hack/PLANNING_A_TO_Z.md#L101-L120) Section 3.2.

---

## Decision Matrix

| Field | Required Content & Locked Decision |
|---|---|
| **Challenge ID** | `CAT-HACK-REF-01` (Reference Industrial Telematics & Asset Decision Support) |
| **Exact statement** | *"Develop an intelligent, trustworthy decision-support system for heavy equipment fleet managers and field technicians to triage machine faults, monitor asset health, and recommend verified, safe maintenance actions before catastrophic failure occurs."* |
| **Official rules** | Pre-event planning authorized; all application code written during event window; open-source standard libraries permitted; no physical machinery control; strict attribution. |
| **Judging rubric** | 1. **Operational Impact & Feasibility (30%)**: Solves real downtime/cost problem.<br>2. **Technical Architecture & Completeness (25%)**: Clean modular monolith, robust testing, deterministic replay.<br>3. **Trust, Safety & UX (25%)**: Clear provenance, evidence citations, human confirmation, offline resilience.<br>4. **Presentation & Live Demo (20%)**: Proof-carrying hero workflow, zero demo crashes, clear metrics. |
| **Primary user** | **Maintenance Supervisor / Field Lead** operating across connected assets and remote job sites, managing multiple machines under time pressure and intermittent network coverage. |
| **Decision/job** | Triaging incoming telemetry alerts and diagnostic fault codes (SPN/FMI) to decide whether to: (a) dispatch emergency field service, (b) schedule routine shop maintenance, or (c) request fluid/oil sampling. |
| **Current failure** | Alert fatigue from raw sensor noise; critical early warnings obscured by low-severity events; lack of historical context leading to delayed decisions or unnecessary expensive field dispatches ($5,000+ per false dispatch, $50,000+ per catastrophic engine failure). |
| **Target outcome** | Reduce fault triage time from >30 minutes to <2 minutes per incident; provide clear diagnostic evidence; enforce 100% human-verified work order creation with full audit logging. |
| **Permitted inputs** | Synthetic telematics streams conforming to ISO 15143-3 (AEMP 2.0) telematics standard (GPS, engine hours, fuel rate, coolant temp, oil pressure); J1939-style diagnostic trouble codes (SPN/FMI); asset specification profiles; historical service logs. |
| **Hero behavior** | **Evidence-Based Fault Triage to Verified Work Order:**<br>1. Ingest telemetry stream & active diagnostic faults.<br>2. Validate data quality (detect stale, missing, or out-of-range sensor readings).<br>3. Contextualize asset historical operating hours & prior maintenance records.<br>4. Run deterministic rule-based severity evaluation.<br>5. Generate an evidence-backed maintenance recommendation with explicit confidence and sensor citations.<br>6. Present recommendation to human supervisor for review and one-click confirmation.<br>7. Generate immutable audit event and dispatch actionable work order. |
| **Supporting behaviors** | 1. **Fleet Health Workspace:** Interactive telemetry trend visualizer with real-time sensor quality & freshness badges.<br>2. **Offline Field Queue:** Local queue allowing field supervisors to review alerts, draft work orders, and reconcile on reconnect. |
| **Trust boundary** | Strict advisory boundary. Every recommendation cites exact triggering telemetry parameters and thresholds. Consequential work orders require explicit human confirmation. Full tamper-evident audit trail. |
| **Cartridge** | **Cartridge 1: Asset Uptime and Maintenance** (VisionLink / Cat Inspect style workflow). |
| **Success measures** | - **Deterministic Execution:** 100% reproducible test suite & demo script from clean reset.<br>- **Performance:** <100ms API response for asset evaluation.<br>- **Reliability:** Graceful degradation on missing sensor data.<br>- **Test Coverage:** Green unit, contract, and integration tests across domain logic. |
| **Non-goals** | - Autonomous equipment control (no engine shutdown commands, no CAN bus injection).<br>- Universal J1939 fault severity translation across all manufacturers.<br>- Real biometrics or external OAuth dependencies for demo.<br>- Unconstrained LLM generation without deterministic grounding. |
| **Cut order** | 1. External voice integration (ElevenLabs).<br>2. Offline sync conflict resolution (fall back to online-first draft mode).<br>3. Predictive ML model integration (rely on deterministic rule engine). |
| **Activated options** | Local deterministic storage profile; modular monolith; React/Next.js UI; Recharts visualization; Vitest test harness. |
| **Rejected options** | Hosted Supabase/Postgres (deferred); Python FastAPI microservice (unnecessary complexity); LangGraph/multi-agent framework (unjustified overhead); Twilio SMS; Mapbox/GIS. |
