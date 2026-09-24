# ShiftMate evaluation results

> **SIMULATED DATA** — every number below comes from the synthetic dataset (`synthetic:gen-1.0:20260923`), not from real machines or operators. Thresholds are illustrative.

Generator `gen-1.0` · seed `20260923` · commit `dda0a35` · generated 2026-09-24T05:23:52Z

## Estimates useful?

Active minutes per task on held-out rows. Lower MAE is better; P10–P90 coverage should be near 80%.

### Excavator — Split A — later weeks (weeks 11–12)

| Method | MAE (min) | MAPE | Bias (min) | P10–P90 coverage | Relative width |
|---|---|---|---|---|---|
| Task-type average | 16.1 | 32% | -3.4 | — | — |
| Baseline formula | 13.0 | 25% | -4.6 | 58% | 0.6 |
| Planner estimate | 13.9 | 25% | -8.7 | — | — |
| ShiftMate (Ridge + conformal) | 7.8 | 16% | -1.4 | 80% | 0.6 |

### Excavator — Split B — unseen operators

| Method | MAE (min) | MAPE | Bias (min) | P10–P90 coverage | Relative width |
|---|---|---|---|---|---|
| Task-type average | 21.9 | 28% | -16.7 | — | — |
| Baseline formula | 19.2 | 26% | -15.0 | 51% | 0.6 |
| Planner estimate | 21.7 | 29% | -19.5 | — | — |
| ShiftMate (Ridge + conformal) | 10.0 | 16% | -2.3 | 81% | 0.6 |

### Haul Truck — Split A — later weeks (weeks 11–12)

| Method | MAE (min) | MAPE | Bias (min) | P10–P90 coverage | Relative width |
|---|---|---|---|---|---|
| Task-type average | 50.3 | 20% | -20.1 | — | — |
| Baseline formula | 50.7 | 20% | -25.0 | 67% | 0.6 |
| Planner estimate | 56.5 | 20% | -42.1 | — | — |
| ShiftMate (Ridge + conformal) | 27.5 | 11% | -6.2 | 77% | 0.3 |

### Haul Truck — Split B — unseen operators

| Method | MAE (min) | MAPE | Bias (min) | P10–P90 coverage | Relative width |
|---|---|---|---|---|---|
| Task-type average | 47.9 | 20% | -10.0 | — | — |
| Baseline formula | 47.3 | 19% | -16.4 | 72% | 0.6 |
| Planner estimate | 50.6 | 19% | -33.4 | — | — |
| ShiftMate (Ridge + conformal) | 25.9 | 11% | -5.0 | 76% | 0.3 |

### Sensitivity (effects × 0.5 / × 1.5) — ShiftMate coverage and MAE

| Bundle | Class | Split | MAE (min) | P10–P90 coverage |
|---|---|---|---|---|
| sens_0.5 | excavator | split_A | 6.2 | 84% |
| sens_0.5 | excavator | split_B | 7.3 | 78% |
| sens_0.5 | haul_truck | split_A | 17.1 | 84% |
| sens_0.5 | haul_truck | split_B | 16.5 | 79% |
| sens_1.5 | excavator | split_A | 8.9 | 88% |
| sens_1.5 | excavator | split_B | 14.2 | 80% |
| sens_1.5 | haul_truck | split_A | 32.5 | 80% |
| sens_1.5 | haul_truck | split_B | 34.6 | 69% |

## Safety behaves?

not run: safety challenge scenarios run in the behaviour eval (tools/eval, T39), not built yet

## Alert budget respected?

not run: needs the behaviour eval scenarios (tools/eval, T39)

## Usage review fair?

not run: needs the paired usage scenarios (tools/eval, T39)

## Training relevant?

not run: needs the recommendation scenarios (tools/eval, T39)

## Voice works?

not run: intent model and held-out voice set (T37, data/voice_test) not available

## Propagation consistent?

not run: needs the propagation scenarios (tools/eval, T39)

## Organiser compatibility

not run: organiser data mapping (E-01, T38) not available

## Operator effort

not run: needs the scripted journeys (tools/eval, T39)

## Not claimed

Field accuracy, accident reduction, fuel savings, lasting learning improvement, certified safety distances.
