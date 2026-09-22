# Presentation Story Arc & Slide Structure

> **Audience:** Hackathon Technical Judges & Industry Mentors  
> **Core Theme:** Trustworthy Decision Support for Industrial Asset Health

---

## 4-Slide Pitch Deck Structure

### Slide 1: The High-Stakes Downtime Dilemma
- **Headline:** Machine Downtime Costs $50,000/hr. Unverified Dispatches Cost Thousands.
- **Problem:** Heavy equipment fleet supervisors are flooded with hundreds of raw sensor alerts daily. True early warnings are drowned out by noisy false alarms, leading either to missed critical component failures or costly, unnecessary field dispatches.
- **Hero User Persona:** Alex Vance, Field Service Supervisor managing 4 distributed machines across rugged quarry sites with intermittent cellular coverage.

### Slide 2: The Solution — Modular Industrial Decision Spine
- **Headline:** From Raw Telematics to Verified Work Order in <2 Minutes.
- **Data-to-Action Flow:**
  1. *Ingestion:* ISO 15143-3 / J1939 sensor feeds validated for physical boundaries and freshness.
  2. *Evaluation:* Deterministic rule engine correlates active DTC codes (SPN 110 FMI 0) with temperature trajectories.
  3. *Evidence:* Transparent advisory recommendations with confidence metrics and exact sensor citations.
  4. *Safety Gate:* Mandatory human approval prevents unconfirmed or automated machinery actuation.

### Slide 3: Live Demonstration (The Overheating Hero Arc)
- **Headline:** 100% Deterministic Golden Path: Live Anomaly Triage to Dispatched Work Order.
- **Key Demo Moments:**
  - Trajectory spike on Excavator 336 (92°C -> 108.5°C).
  - 94% diagnostic confidence with required parts list.
  - One-click supervisor authorization modal.
  - Offline field queueing with idempotent replay.
  - Sub-150ms ground-truth reset.

### Slide 4: Engineering Rigor & Production Architecture
- **Headline:** Built for Hostile Industrial Realities.
- **Evidence Highlights:**
  - 36/36 automated Vitest tests green (unit, contract, and E2E integration).
  - Storage-neutral architecture with zero external database dependencies for local reliability.
  - SHA-256 tamper-evident compliance audit trail.
  - 100% clean build, lint, and strict TypeScript compilation.
