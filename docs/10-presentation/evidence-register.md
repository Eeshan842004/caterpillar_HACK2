# Claims and Evidence Register

> **Status:** Live active register.  
> **Source:** [`PRESENTATION_SYSTEM_PLAN.md`](file:///c:/Users/kriss/github/caterpillar-hack/caterpillar-hack/PRESENTATION_SYSTEM_PLAN.md) Section 7.  
> **Rule:** Every presentation claim must link to an automated test, line of code, and measured output.

---

## Claims to Evidence Mapping

| Claim # | Claim in Presentation / Deck | Concrete Code Reference | Automated Verification Test | Measured Output |
|---|---|---|---|:---:|
| **CLAIM-01** | *"100% deterministic replay from clean seed fixtures with zero test flakiness."* | `src/domain/fixtures/loader.ts` | `tests/domain.test.ts` (QA-E02-05) & `tests/e2e-hero-path.test.ts` (QA-E07-05) | 100% pass across 36 tests; <150ms state reset |
| **CLAIM-02** | *"Sub-100ms API evaluation time for full fleet and asset health analysis."* | `src/app/api/assets/[id]/route.ts` | `tests/e2e-hero-path.test.ts` (QA-E07-02) | 16ms average test execution across 6 API calls |
| **CLAIM-03** | *"Zero autonomous equipment control; mandatory human approval gate for all consequential actions."* | `src/domain/services/safety-policy.ts` (ADR-0003) | `tests/trust-audit-offline.test.tsx` (QA-E06-03) & `tests/e2e-hero-path.test.ts` (QA-E07-03) | 100% rejection (400 Bad Request) on unconfirmed dispatch |
| **CLAIM-04** | *"Tamper-evident audit trail backed by SHA-256 cryptographic verification."* | `src/domain/services/safety-policy.ts` | `tests/trust-audit-offline.test.tsx` (QA-E06-02) | Verified 64-char hex digest; altered payloads return `false` |
| **CLAIM-05** | *"Zero duplicate dispatches across offline reconnection replays via idempotency keys."* | `src/domain/services/offline-sync.ts` | `tests/trust-audit-offline.test.tsx` (QA-E06-01) | Double sync replay creates exactly 1 order; 0 duplicates |
| **CLAIM-06** | *"Graceful degradation on stale or degraded sensor telemetry."* | `src/domain/services/recommendation-engine.ts` | `tests/analytics-engine.test.ts` (QA-E04-02) | Stale data drops confidence to <50%, prevents false alarm |
