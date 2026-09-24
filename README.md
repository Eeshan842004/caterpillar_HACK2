# ShiftMate

**ShiftMate** is an offline-first, operator-first in-cab companion for Cat machine operators (excavators and haul trucks), paired with a local site server and a web console for supervisors, trainers, safety coordinators and mechanics.

## Documentation
- [Product Plan](docs/PRODUCT_PLAN.md): product requirements, user journeys and feature specifications (source of truth for behaviour).
- [Technical Specification](docs/TECHNICAL_SPEC.md): architecture, schema, contracts and implementation plan.
- [Dataset Schema](docs/DATASET_SCHEMA.md): the generated synthetic dataset.
- [Frontend Plan](docs/FRONTEND_PLAN.md): what the current operator-app slice contains and what comes next.
- [Generator Assumptions](docs/GENERATOR_ASSUMPTIONS.md): generator effects, calibration and sensitivity runs (generated).
- [Future Ideas](docs/FUTURE_IDEAS.md): parked ideas, not part of the build.

## Repository layout
- `apps/operator`: Expo SDK 57 operator app (Android primary, web build for judges and tests).
- `packages/core`: pure TypeScript engine — machine state, safety rules, Safe Exit Guard, alerts, tasks, estimation, idle review, ledger, simulator.
- `packages/content`: machine profiles, demo seed and demo history.
- `server/`: FastAPI site server (`shiftmate`) and the data generator (`shiftmate_ml`).
- `data/`: generator config and generated dataset bundles (`data/generated` is git-ignored).

## Quick start

Prerequisites: Node 22 + pnpm 10.34.5, Python 3.12 + uv.

```bash
pnpm install
pnpm py:sync

# Server config: copy the example and set a real device master key
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # paste as DEVICE_SECRET_MASTER_KEY
# Local development without Docker: DATABASE_URL=sqlite:///./var/shiftmate.db and DEMO_MODE=true

cd server && uv run python -m shiftmate.cli seed && cd ..     # create and seed the database
pnpm server:dev                                               # http://localhost:8000/api/v1/health

pnpm ml:generate                                              # dataset bundle + validation gates
pnpm operator:web                                             # operator app in the browser
```

In the operator app: pair **EX-07** (Local only), sign in as **Ravi** with PIN **1234** using only the keyboard (arrows, Enter, digits, Space = ACK, M = menu). Press **F2** for the presenter panel that drives the simulated machine (dig, belt, door, proximity, rain, fast-forward).

## Checks

```bash
pnpm -r --if-present typecheck      # content, core, operator
pnpm -r --if-present test           # core engine (Vitest)
pnpm server:test                    # server + dataset (pytest)
pnpm --filter @shiftmate/operator export:web
```

All results come from simulated machine data and a synthetic dataset; they are not field results.
