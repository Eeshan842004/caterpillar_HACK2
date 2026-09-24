# Agent B — server, data, ML (do now)

Read `AGENTS.md` first. You own `server/**`, `data/**`, `docker/**`, `docker-compose.yml`, `packages/content/models/**`, `packages/content/seed/demo_history.json` and the contract docs. Do B1 first (Agent A waits on it for A6).

Current state: FastAPI server (20 tests), dataset generator with strengthened gates, SQLite for local dev, no Alembic, no scenarios/WebSocket/static hosting.

## B1. Contract fix + trained estimator (T36, §5.4.4, §8.6.2–8.6.4, §8.22)
- Contract: add `task_type` to the `inference/estimate` payload (§5.3.2 table, `EstimatePayload` in `server/shiftmate/schemas/ledger.py`, generator `timeline.py`, DATASET_SCHEMA §4.5). Reason: the device cannot compute expected waiting from history without it (§8.6.5). Regenerate the bundle; all gates must pass.
- `server/shiftmate_ml/train/{estimator.py,export.py}`: per class, the exact §8.6.2 encoding (reference levels dropped, numeric standardised with training stats), `RidgeCV(alphas=[0.1,0.3,1,3,10,30], cv=5)` on `training_eligible` rows, target `ln(actual_active_min / baseline_minutes)`; split A ships, split B reported; conformal quantiles per §8.6.4 (pooled + by task type).
- Write `packages/content/models/estimator.{excavator,haul_truck}.v1.json` (schema §5.4.4) and `models/parity/estimator.<class>.golden.json` (50 test rows: raw inputs + p10/p50/p90).
- `shiftmate.cli publish-models` loads them into `model_artifacts`.
- `server/shiftmate_ml/eval/estimates.py` → `eval/results/estimates.json`: MAE, MAPE, P10–P90 coverage, relative width, bias per class/task type vs task-type average, baseline, planner; also on `sens_0.5` and `sens_1.5`.
- **Done when:** TC-63 (calibration coverage 0.80 ± 0.08) passes; the artifact's factors include weather and skill; tell Agent A the files are ready.

## B2. Alembic + Postgres readiness (T20, §5.2, §10.4)
- `server/alembic.ini`, `alembic/env.py`, `alembic/versions/0001_initial.py` with explicit DDL matching `models.py` (CHECKs, partial unique indexes). Add `psycopg[binary]==3.3.6`; pin the §3.3 versions in `pyproject.toml` and update `uv.lock`.
- `docker-compose.yml` + `docker/postgres-init/01-create-test-db.sql` + `docker/api.Dockerfile` per §10.4.
- **Done when:** `alembic upgrade head` on a fresh SQLite file, then `alembic check` reports no differences. Report the Postgres run as "not executed: Docker not installed on this machine".

## B3. Near-miss → scenario pipeline, server side (T31 server part, §8.23, M12)
- `services/scenarios.py`: templates `T-EX-PERSON`, `T-EX-VEHICLE`, `T-HT-PERSON`, `T-HT-LV`, `T-GENERIC`, en + hi bodies, anonymised, `scenario_id = "nm-" + sha256(incident_id)[:8]`.
- Draft on safety review when the final type is `near_miss` (replace the "T31" comment in `routers/console_incidents.py`) and on send-to-trainer.
- `routers/console_scenarios.py`: list, detail, PUT (draft only), approve → `scenario.published` change (scope `machine_class`), reject, redraft (`template`; `llm` → 409 "AI unavailable").
- **Done when:** TC-54 — reviewed near miss → template draft (en + hi) → trainer edit → approve → change visible on `/sync/pull` for an excavator device.

## B4. Console WebSocket (§6.3 WS row, §6.4)
- `routers/console_ws.py`: cookie auth at upgrade (close 4401), ping/pong, hub broadcasting `{"type":"invalidate","keys":[…]}` to sessions whose `site_ids` include the event's site, sent **after commit** (`session.info["after_commit"]`). Projectors and console actions return their invalidation keys.
- **Done when:** TC-61 — pushing a site-delay finding delivers `invalidate ["follow-ups"]` to a connected supervisor socket.

## B5. Static hosting (DR-07, §4.4 `static.py`)
- Mount `/console` (SPA fallback to `index.html`) and `/app` (every response carries COOP `same-origin` + COEP `credentialless`) when `STATIC_CONSOLE_DIR` / `STATIC_OPERATOR_DIR` exist; skip otherwise.
- **Done when:** tests prove the SPA fallback and the `/app` headers.

## Keep green
`uv run pytest`, dataset gates, and `ruff check --select F` on files you touch.
