# Worker Brief — E-04: Baseline Analytics and Recommendations

- **Work-Item ID:** `E-04`
- **Assigned Worker Model:** `gemini-3.8-flash`, thinking level `medium`
- **Coordinator:** `gemini-3.8-flash`, thinking level `high`
- **Branch:** `gemini/E-04-baseline-analytics`
- **Dependencies & Input Commits:** Depends on `E-02` and `E-03` (commit `a1f5256`)

---

## 1. Outcome

A deterministic recommendation engine service that evaluates machine telemetry, operating thresholds, and diagnostic trouble codes to generate advisory maintenance recommendations with explicit evidence citations, confidence scores, and graceful degradation on stale or missing data.

---

## 2. Owned Files & Excluded Files

### Owned Files
- `src/domain/services/recommendation-engine.ts`
- `tests/analytics-engine.test.ts`
- `planning/briefs/E-04-brief.md`

### Excluded Files
- UI components (Owned by `E-05`)
- Next.js Route Handlers (Owned by `E-07`)
- Persistence adapters (Owned by `E-03`)

---

## 3. Exact Requirements & Non-Goals

### Exact Requirements
1. Implement `RecommendationEngine` in `src/domain/services/recommendation-engine.ts`:
   - Evaluates `Asset`, active `DiagnosticFault[]`, and latest `Record<string, TelemetryPoint>`.
   - Generates typed `Recommendation` object conforming to `src/domain/types.ts`.
   - Populates `evidence_citations` containing parameter name, observed value, threshold value, unit, and timestamp.
   - Computes explicit `confidence_score` (0.0 to 1.0).
   - Generates `suggested_work_order` payload for immediate or scheduled human review.
2. Graceful Degradation Rules:
   - Stale or missing data must degrade recommendation urgency to `OBSERVE` or flag *"Insufficient Evidence"*.
   - Low confidence (< 0.50) when data quality is `STALE` or `SUSPECT`.
3. Strict Safety Boundary:
   - All recommendation text is advisory (decision support). Zero command/control directives.
4. Unit tests in `tests/analytics-engine.test.ts`.

### Non-Goals
- Do not call external LLM APIs (Product LLM is disabled in Manifest Section 5).
- Do not generate arbitrary ungrounded diagnostic claims.

---

## 4. Acceptance Criteria

- Hero asset `ast_336_001` receives `EMERGENCY` recommendation with 90%+ confidence and cited coolant readings.
- Stale asset `ast_745_002` receives low-confidence "Insufficient Evidence" recommendation.
- Nominal asset `ast_980_003` receives nominal status with no work order.
- `tests/analytics-engine.test.ts` passes 100%.
