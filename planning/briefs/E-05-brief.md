# Worker Brief — E-05: Operational Workspace

- **Work-Item ID:** `E-05`
- **Assigned Worker Model:** `gemini-3.8-flash`, thinking level `medium`
- **Coordinator:** `gemini-3.8-flash`, thinking level `high`
- **Branch:** `gemini/E-05-operational-workspace`
- **Dependencies & Input Commits:** Depends on `E-02`, `E-03`, `E-04` (commit `cf8f1f4`)

---

## 1. Outcome

An accessible, responsive, premium industrial operational workspace built with Next.js 14, React 18, Recharts, and Vanilla CSS tokens that displays equipment health, live telemetry charts, diagnostic faults, advisory recommendations with citations, and an explicit human-in-the-loop work order confirmation modal.

---

## 2. Owned Files & Excluded Files

### Owned Files
- `src/components/Header.tsx`
- `src/components/AssetSelector.tsx`
- `src/components/TelemetryChart.tsx`
- `src/components/FaultList.tsx`
- `src/components/RecommendationCard.tsx`
- `src/components/ConfirmationModal.tsx`
- `src/components/AuditLogView.tsx`
- `src/components/Workspace.tsx`
- `src/app/page.tsx`
- `tests/workspace-ui.test.tsx`
- `planning/briefs/E-05-brief.md`

### Excluded Files
- API Route handlers (Owned by `E-07`)
- Core domain entities (Owned by `E-02`)

---

## 3. Exact Requirements & Non-Goals

### Exact Requirements
1. **Persona & Governance Header:**
   - Display persona: "Alex Vance — Field Service Supervisor".
   - Site timezone: "Asia/Calcutta".
   - Synthetic Data notice: "SYNTHETIC DEMO DATA — ADVISORY ONLY".
   - Reset Demo button calling reset handler.
2. **Asset Fleet Selector:**
   - Grid/list of assets with status badges (`CRITICAL`, `WARNING`, `NOMINAL`).
   - Clicking an asset updates active selection.
3. **Telemetry & Faults Visualization:**
   - Recharts line chart showing temperature trajectory over time against critical threshold line.
   - Fault list showing SPN/FMI code, severity, and description.
4. **Advisory Recommendation Panel:**
   - Displays recommendation title, urgency, confidence percentage (e.g. 94%), and evidence citations.
5. **Mandatory Human Confirmation Modal:**
   - Accessible modal dialog requiring explicit click to "Confirm & Dispatch Work Order".
   - Captures notes and technician assignment.
6. **Audit Trail & Work Order Viewer:**
   - View newly dispatched work orders and immutable audit events.

### Non-Goals
- Do not use TailwindCSS.
- Do not connect to real physical machinery.
- Do not add unauthorized Caterpillar logos or trade dress.

---

## 4. Acceptance Criteria

- All components render cleanly with zero React hydration errors.
- Chart displays temperature curve and threshold line.
- Confirmation modal opens and allows work order submission.
- `tests/workspace-ui.test.tsx` passes 100%.
