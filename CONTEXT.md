# CONTEXT.md — Live Status and Active Handoffs

> **Last updated:** 2026-09-22, Asia/Calcutta
>
> **Phase:** Pre-event starter preparation
>
> **Status:** P1 reusable-core and cartridge separation implemented and verified
>
> **Official problem statement:** Not received

## Current truth

- This repository is a starter foundation, not an official submission.
- `src/core` is challenge-neutral and contains evidence, determinism, safety and offline
  contracts.
- `src/cartridges/asset-maintenance` is a worked reference cartridge.
- `examples/asset-maintenance` preserves its mock planning, QA, reviews and presentation.
- Live reveal files under `planning/` are intentionally unresolved and block implementation
  of an official challenge.
- Authentication, hosted persistence, ElevenLabs, product LLM/RAG, maps, notifications and
  deployment remain disabled until an approved manifest activates them.

## Current objective

Freeze the verified starter boundary until official rules and the problem statement arrive.

## Current scope

In scope:

- challenge-neutral core;
- asset-maintenance reference isolation;
- portable repository-relative documentation;
- live reveal templates;
- non-fleet adaptation drill;
- test, type, lint and build verification.

Out of scope:

- guessing the official problem;
- presenting the reference cartridge as event-created or submitted;
- activating external providers without challenge evidence;
- physical machinery control;
- production-readiness claims.

## Current architecture

```text
live planning templates
        ↓
challenge-neutral core
        ↓
selected/created cartridge
        ↓
application routes and UI
        ↓
tests, evidence, demo and presentation
```

## Known limitations

- The default workspace consumes the API-backed state path, but no running-browser E2E suite
  currently verifies the complete rendered flow.
- The generic offline queue is not durable across process/page restart.
- Audit hashing is a verification utility, not an immutable ledger.
- The reference evidence and timing claims must not be reused as live challenge evidence.
- Competition rules and prework eligibility remain unverified.

## Next decision points

1. Obtain official competition rules and record sources.
2. Receive the official problem statement.
3. Complete the live Challenge Compiler.
4. Select or create a cartridge.
5. Complete and approve the live Implementation Manifest.
6. Only then authorize challenge implementation.

## Read next

1. `STARTER_PACK_GUIDE.md`
2. `planning/rules-and-provenance.md`
3. `planning/challenge-compiler.md`
4. `planning/implementation-manifest.md`
5. `planning/lock-trigger-register.md`
6. `PLANNING_A_TO_Z.md`
