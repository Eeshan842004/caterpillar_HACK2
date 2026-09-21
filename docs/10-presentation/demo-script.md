# Live Judging Demo Script — Equipment Operations Workspace

> **Allocated Duration:** 4 Minutes Total (2.5 min presentation + demo, 1.5 min technical Q&A)  
> **Persona:** Alex Vance (Field Service Supervisor, North Quarry Operations)  
> **Target Outcome:** Prove automated telematics triage, transparent evidence citations, mandatory human safety gate, and deterministic replay.

---

## Minute-by-Minute Run of Show

### Minute 0:00 – 0:45 | Problem & Operational Context
- **Speaker:** "Heavy equipment fleet managers face severe alert fatigue. Hundreds of raw sensor events stream in daily, obscuring critical early warnings. Missing an escalating engine overheating condition leads to catastrophic failure ($50,000+ per machine), while false dispatches cost thousands. We built the Equipment Operations Workspace—a transparent, modular decision-support spine."
- **Visual:** Open application at `http://localhost:3000`. Point out the neutral industrial theme, active demo persona, and "SYNTHETIC DEMO DATA" compliance badge in the header.

### Minute 0:45 – 1:30 | The Incident (Hero Anomaly Arc)
- **Action:** Click on asset card **CAT-336-HEX-8821** with red `CRITICAL` badge.
- **Speaker:** "Here in our North Quarry site, Excavator 336 has triggered an automated alert. Look at the real-time telemetry chart: coolant temperature has escalated over the past 30 minutes from 92°C to 108.5°C, breaching the 102°C warning threshold. Concurrently, the engine controller emitted J1939 Diagnostic Trouble Code `SPN 110 FMI 0`."
- **Visual:** Hover over the Recharts temperature trajectory, pointing to the dashed threshold lines.

### Minute 1:30 – 2:15 | Advisory Decision Support & Safety Compliance Gate
- **Speaker:** "Rather than a black-box AI recommendation, our engine generates an evidence-backed advisory diagnosis with 94% confidence, citing exact sensor timestamps and thresholds. Crucially, under industrial safety standard ADR-0003, our system NEVER commands physical machinery autonomously. It provides decision support."
- **Action:** Click **"Review & Confirm Work Order →"**.
- **Visual:** Confirmation modal pops up with prominent **"SAFETY COMPLIANCE GATE"** badge.
- **Speaker:** "Notice the human-in-the-loop gate. The supervisor reviews the proposed emergency hose kit, assigns lead technician Marcus Brody, enters authorization notes, and explicitly authorizes dispatch."
- **Action:** Click **"Authorize & Dispatch Work Order"**.
- **Visual:** Modal closes; new entry immediately populates in Dispatched Work Orders and the immutable Audit Trail.

### Minute 2:15 – 2:45 | Offline Resilience & Tamper-Evident Audit
- **Speaker:** "In remote mines, connectivity drops frequently. Watch this: we simulate field offline mode."
- **Action:** Click **"Simulate: Go Offline"**.
- **Visual:** Banner turns amber: *"Field Offline Mode (Local Storage Active)"*.
- **Speaker:** "Technicians can draft emergency repairs offline. When reconnection occurs, our idempotent sync queue reconciles the order without duplicate dispatch. Furthermore, every audit event is sealed with a SHA-256 cryptographic hash to guarantee compliance integrity."

### Minute 2:45 – 3:00 | Instant Reset & Conclusion
- **Speaker:** "Finally, our architecture guarantees 100% deterministic replay. One click restores pristine ground truth."
- **Action:** Click **"↺ Reset Demo State"**.
- **Visual:** State cleanly resets in 150ms back to seed baseline.
- **Speaker:** "Thank you. We are ready for technical Q&A."

---

## Quick Reset Procedure
If demo state needs resetting during rehearsals or between judging tables:
1. Click the header button **"↺ Reset Demo State"**, OR
2. In terminal: `curl -X POST http://localhost:3000/api/admin/reset`
