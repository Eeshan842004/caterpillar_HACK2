# Agent instructions (ShiftMate)

## Sources of truth
- Product behaviour: `docs/PRODUCT_PLAN.md`. Architecture, contracts, algorithms, task IDs (T01–T51): `docs/TECHNICAL_SPEC.md`. Generated data: `docs/DATASET_SCHEMA.md`. Current frontend slice: `docs/FRONTEND_PLAN.md`.
- Implement exactly what the spec says. If the spec is impossible or contradicts the code/data, stop that item and report the conflict, the requirement IDs and the smallest fix. Do not redesign or add features that are not in the spec.
- `docs/FUTURE_IDEAS.md` is **not** part of the build. Never implement it.

## Work split (two agents in parallel)
- **Agent A — operator app:** owns `apps/operator/**`, `packages/core/**`. Brief: `docs/codex/AGENT_A_OPERATOR.md`.
- **Agent B — server, data, ML:** owns `server/**`, `data/**`, `docker/**`, `docker-compose.yml`, `packages/content/models/**`, `packages/content/seed/demo_history.json`, and the contract docs (`docs/TECHNICAL_SPEC.md` §5.3.2, `docs/DATASET_SCHEMA.md`). Brief: `docs/codex/AGENT_B_SERVER.md`.
- Do not edit the other agent's paths. If you need a contract change, say so in your report; Agent B owns contracts.

## Rules
- `packages/core` stays pure TypeScript: no React/Expo/`fetch`/timers/`Date.now`/`Math.random`. Clock and IDs are injected.
- Every ledger payload must validate against `server/shiftmate/schemas/ledger.py::validate_ledger_payload` (§5.3.2). `alert` and `inference` entries need `rule_or_model_version`.
- Pin versions from spec §3. Expo packages only via `npx expo install` (inside `apps/operator`).
- Never commit secrets, `.env`, databases or build output. Do not push or open PRs unless asked.
- Timestamps: epoch ms inside core/device; ISO-8601 UTC with ms and `Z` on the wire; site-local = UTC + `utc_offset_minutes`.

## Checks (all must stay green)
```bash
pnpm -r --if-present typecheck
pnpm -r --if-present test                       # packages/core Vitest
cd server && uv run pytest                      # server + dataset
cd server && uv run python -m shiftmate_ml.datagen.generate --all-sensitivities   # dataset gates
pnpm --filter @shiftmate/operator export:web    # web bundle builds
```
Local server: copy `.env.example` → `.env`, set a 64-hex `DEVICE_SECRET_MASTER_KEY`, `DATABASE_URL=sqlite:///./var/shiftmate.db`, `DEMO_MODE=true`, then `cd server && uv run python -m shiftmate.cli seed && uv run uvicorn shiftmate.main:app --port 8000`.

## Reporting
End with: tasks done (spec task IDs), files changed, each check as "run + result" or "not run + reason", anything blocked. Never say a test passed unless you ran it.
