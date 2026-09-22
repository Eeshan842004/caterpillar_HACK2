# Claims and Evidence Register

> **Status:** Live active register.  
> **Source:** `PRESENTATION_SYSTEM_PLAN.md` Section 7.  
> **Rule:** Every presentation claim must link to an automated test, line of code, and measured output.

---

## Claims to Evidence Mapping

| Claim # | Claim in Presentation / Deck | Concrete Code Reference | Automated Verification Test | Measured Output |
|---|---|---|---|:---:|
| **CLAIM-01** | *"100% deterministic fixture reset with no observed test flakiness in the recorded run."* | `src/cartridges/asset-maintenance/domain/fixtures/loader.ts` | `tests/cartridges/asset-maintenance/domain.test.ts` (QA-E02-05) & `tests/cartridges/asset-maintenance/e2e-hero-path.test.ts` (QA-E07-05) | Historical mock run: 36 tests passed; runtime-generated IDs/timestamps were not deterministic |
| **CLAIM-02** | *"Fast in-process route-handler evaluation in the recorded mock run."* | `src/app/api/assets/[id]/route.ts` | `tests/cartridges/asset-maintenance/e2e-hero-path.test.ts` (QA-E07-02) | Historical 16ms test execution; not an HTTP/load-test result |
| **CLAIM-03** | *"No autonomous equipment control; mandatory human approval gate for dispatch."* | `src/core/safety/consequential-action-policy.ts` and the cartridge wrapper | `tests/cartridges/asset-maintenance/trust-audit-offline.test.tsx` (QA-E06-03) | Unconfirmed dispatch rejected in tested route/profile |
| **CLAIM-04** | *"SHA-256 tamper-detection utility for audit payloads."* | `src/core/safety/consequential-action-policy.ts` | `tests/cartridges/asset-maintenance/trust-audit-offline.test.tsx` (QA-E06-02) | Altered payload fails verification; this is not an immutable external ledger |
| **CLAIM-05** | *"No duplicate dispatch in repeated in-memory queue replay test."* | `src/core/offline/offline-action-queue.ts` and cartridge sync service | `tests/cartridges/asset-maintenance/trust-audit-offline.test.tsx` (QA-E06-01) | One in-memory replay test; queue is not durable across restart |
| **CLAIM-06** | *"Graceful degradation on stale sensor telemetry in the reference rule engine."* | `src/cartridges/asset-maintenance/domain/services/recommendation-engine.ts` | `tests/cartridges/asset-maintenance/analytics-engine.test.ts` (QA-E04-02) | Stale fixture lowers confidence below 50% |
