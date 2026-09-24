# ShiftMate Synthetic Dataset Generator Assumptions

**Generator Version:** `gen-1.0`  
**Schema Version:** `1.2.0`  
**Random Seed:** `20260923`  
**Anchor Date:** `2026-09-22`  
**Data Origin:** `synthetic:gen-1.0:20260923`  

> [!IMPORTANT]
> These parameters and multipliers are starting assumptions for synthetic prototype evaluation.
> They do **not** represent measured physical Caterpillar telemetry or certified machine operational rates.

## 1. Task Duration Model & Effects

The actual active duration of a task is modeled as:
```
actual_active_min = baseline_min * exp(sum(effects) + operator_effect + site_effect + noise)
```
where baseline minutes are strictly derived from profile rate constants and site job efficiency (technical spec §8.6.1).

### Effect Magnitudes and Rationales

| Effect Domain | Key / Level | Value (log scale) | Rationale |
|---|---|---|---|
| Skill Level | `beginner` | `+0.30` | Beginners spend more time positioning and cycling (+30%); experts have refined control and cycle rhythm (-5%). |
| Skill Level | `intermediate` | `+0.00` | Beginners spend more time positioning and cycling (+30%); experts have refined control and cycle rhythm (-5%). |
| Skill Level | `expert` | `-0.05` | Beginners spend more time positioning and cycling (+30%); experts have refined control and cycle rhythm (-5%). |
| Experience | `coef*(log1p(min(m, 36))-3.0)` | `coef=-0.06` | Learning curve -0.06 * (log1p(min(months, 36)) - 3.0): fast early gains that stop after about three years. The plateau is deliberately NOT the estimator's plain log1p transform, so a linear model cannot fit it exactly. |
| Weather | `clear` | `+0.00` | Adverse weather impairs traction and soil handling. Wind adds +20% extra to wind-sensitive tasks like pipe lifting. |
| Weather | `rain` | `+0.14` | Adverse weather impairs traction and soil handling. Wind adds +20% extra to wind-sensitive tasks like pipe lifting. |
| Weather | `windy` | `+0.10` | Adverse weather impairs traction and soil handling. Wind adds +20% extra to wind-sensitive tasks like pipe lifting. |
| Weather | `windy_sensitive_extra` | `+0.20` | Adverse weather impairs traction and soil handling. Wind adds +20% extra to wind-sensitive tasks like pipe lifting. |
| Weather | `dusty` | `+0.07` | Adverse weather impairs traction and soil handling. Wind adds +20% extra to wind-sensitive tasks like pipe lifting. |
| Weather | `foggy` | `+0.09` | Adverse weather impairs traction and soil handling. Wind adds +20% extra to wind-sensitive tasks like pipe lifting. |
| Visibility | `good` | `+0.00` | Reduced visibility slows down haul speeds and swinging operations due to cautious maneuvering. |
| Visibility | `moderate` | `+0.04` | Reduced visibility slows down haul speeds and swinging operations due to cautious maneuvering. |
| Visibility | `poor` | `+0.10` | Reduced visibility slows down haul speeds and swinging operations due to cautious maneuvering. |
| Temperature | `cool` | `+0.00` | Extreme ambient heat (>38C) places stress on cooling systems and causes operators to pace work more conservatively. |
| Temperature | `mild` | `+0.00` | Extreme ambient heat (>38C) places stress on cooling systems and causes operators to pace work more conservatively. |
| Temperature | `hot` | `+0.03` | Extreme ambient heat (>38C) places stress on cooling systems and causes operators to pace work more conservatively. |
| Temperature | `extreme` | `+0.08` | Extreme ambient heat (>38C) places stress on cooling systems and causes operators to pace work more conservatively. |
| Time of Day | `morning` | `+0.00` | Night operations suffer from directional shadow glare and circadian fatigue, adding ~6% to cycle duration. |
| Time of Day | `afternoon` | `+0.00` | Night operations suffer from directional shadow glare and circadian fatigue, adding ~6% to cycle duration. |
| Time of Day | `evening` | `+0.03` | Night operations suffer from directional shadow glare and circadian fatigue, adding ~6% to cycle duration. |
| Time of Day | `night` | `+0.06` | Night operations suffer from directional shadow glare and circadian fatigue, adding ~6% to cycle duration. |
| Site Congestion | `low` | `+0.00` | Congested worksites introduce queueing at crossings, loading pockets, and dump ramps (+11% high congestion). |
| Site Congestion | `medium` | `+0.04` | Congested worksites introduce queueing at crossings, loading pockets, and dump ramps (+11% high congestion). |
| Site Congestion | `high` | `+0.11` | Congested worksites introduce queueing at crossings, loading pockets, and dump ramps (+11% high congestion). |
| Machine Age | per year | `+0.012` | Wear in linkages, minor hydraulic throttling, and aging components degrade cycle efficiency by 1.2% per year of age. |
| Material | `clay` | `+0.00` | Hard rock and abrasive ore resist penetration and require higher breakout effort (+5%). |
| Material | `sand` | `+0.00` | Hard rock and abrasive ore resist penetration and require higher breakout effort (+5%). |
| Material | `gravel` | `+0.00` | Hard rock and abrasive ore resist penetration and require higher breakout effort (+5%). |
| Material | `topsoil` | `+0.00` | Hard rock and abrasive ore resist penetration and require higher breakout effort (+5%). |
| Material | `rock` | `+0.05` | Hard rock and abrasive ore resist penetration and require higher breakout effort (+5%). |
| Material | `overburden` | `+0.00` | Hard rock and abrasive ore resist penetration and require higher breakout effort (+5%). |
| Material | `ore` | `+0.05` | Hard rock and abrasive ore resist penetration and require higher breakout effort (+5%). |
| Interaction | `rain_clay_trenching` | `+0.10` | Effects that only appear together (wet clay trench walls, a new operator at night or in rain, queueing trucks on a congested pit). A main-effects Ridge model cannot represent them exactly, which keeps the evaluation from being circular (product §19) and gives the LightGBM comparison (S7) something real to find. |
| Interaction | `beginner_night` | `+0.12` | Effects that only appear together (wet clay trench walls, a new operator at night or in rain, queueing trucks on a congested pit). A main-effects Ridge model cannot represent them exactly, which keeps the evaluation from being circular (product §19) and gives the LightGBM comparison (S7) something real to find. |
| Interaction | `beginner_rain` | `+0.08` | Effects that only appear together (wet clay trench walls, a new operator at night or in rain, queueing trucks on a congested pit). A main-effects Ridge model cannot represent them exactly, which keeps the evaluation from being circular (product §19) and gives the LightGBM comparison (S7) something real to find. |
| Interaction | `high_congestion_haul` | `+0.06` | Effects that only appear together (wet clay trench walls, a new operator at night or in rain, queueing trucks on a congested pit). A main-effects Ridge model cannot represent them exactly, which keeps the evaluation from being circular (product §19) and gives the LightGBM comparison (S7) something real to find. |
| Operator Variance | Gaussian sigma | `N(0, 0.06)` | Persistent individual operator style and pacing differences modeled as N(0, 0.06). |
| Site Variance | Gaussian sigma | `N(0, 0.04)` | Site-specific layout, gradient, and haul road maintenance factors modeled as N(0, 0.04). |
| Residual Noise | heteroscedastic, heavy-tailed | `sigma = 0.1 + 0.1*exp(-baseline/40)`; disruption p=0.03 adds U(0.25, 0.6) | Heteroscedastic, heavy-tailed noise: sigma = 0.10 + 0.10 * exp(-baseline/40), so short tasks vary more in relative terms, plus a 3% chance of an unmodelled disruption adding +0.25..0.60 (log). Constant Gaussian noise would make conformal P10-P90 ranges look perfectly calibrated by construction. |

### Calibration

Per-class log offset: `{'excavator': -0.2, 'haul_truck': -0.38}`. Profile rates are rated (best-case) values, and the summed condition, skill and congestion effects push the synthetic mean far above the organiser evidence (planner MAPE 13.2%, planner under-estimates on average; product §2.2). A per-class constant log offset re-centres mean actual/baseline to about 1.05 without changing any effect size or the relative ranking of conditions. It is a calibration, not a finding.

Resulting check (seed run): mean actual/baseline ≈ 1.08 for both classes; excavator planner bias ≈ +10 min on a 43-minute median task (organiser: +6 min). Planner MAPE is ≈ 21–24%, higher than the organiser's 13.2%, because the synthetic set spans far more conditions than the organiser's five task rows; the spread is kept so the estimator has condition effects to learn. Re-tune once the full organiser data (E-01) is available.

## 2. Dispatch Planner & Waiting Delays

- **Planner Estimate:** `baseline_min * 0.92 * exp(N(0, 0.08))`. Dispatch planners systematically plan ~8% faster than actuals by ignoring weather and congestion variations.
- **Wait Arrivals:** Poisson process with rate lambda per task type. Queues follow Poisson arrivals scaled by site congestion (x0.7 / x1.0 / x1.5) and rain (x1.3), with lognormal durations (median 9 min). 85% are reported. Reasons depend on the task: truck loading mostly waits for trucks; haul trucks queue at the shovel and crusher. 6% of reported reasons are later corrected by the operator (explain-once history).
- **Wait Durations:** Lognormal distribution (median 9.0 min, sigma 0.5).
- **Reporting Ratio:** 85% reported by operator, 15% unexplained.
- **Wait rate modifiers:** congestion `{'low': 0.7, 'medium': 1.0, 'high': 1.5}`, rain x1.3.
- **Reason mix by task type:** `{'truck_loading': {'waiting_truck': 0.55, 'access_blocked': 0.1, 'instructed_hold': 0.1, 'break': 0.15, 'other': 0.1}, 'trenching': {'waiting_truck': 0.15, 'access_blocked': 0.3, 'instructed_hold': 0.25, 'break': 0.2, 'other': 0.1}, 'backfilling': {'waiting_truck': 0.4, 'access_blocked': 0.15, 'instructed_hold': 0.15, 'break': 0.2, 'other': 0.1}, 'grading': {'waiting_truck': 0.1, 'access_blocked': 0.3, 'instructed_hold': 0.3, 'break': 0.2, 'other': 0.1}, 'pipe_lifting': {'waiting_loader': 0.2, 'access_blocked': 0.2, 'instructed_hold': 0.35, 'break': 0.15, 'other': 0.1}, 'haul': {'shovel_queue': 0.4, 'crusher_queue': 0.3, 'access_blocked': 0.08, 'instructed_hold': 0.07, 'break': 0.1, 'other': 0.05}}`.
- **Corrections:** 6% of reported site delays are later corrected to another site delay (explain-once history).

## 3. Required idle, task events and sensors

- **Required idle:** cool-down after heavy loading (p=0.35, 300 s) and cold-start warm-up (p=0.25, 420 s). Cool-down after heavy loading (avg load >= 60% in the task) and cold-start warm-up at shift start are required idle (§8.7): no prompt, no follow-up, never operator waste.
- **Task events:** pause p=0.1, block p=0.03, cancel p=0.015. Some tasks are paused (another instruction), blocked (access, weather, utility mark: counts as waiting, §8.6.7) or cancelled by the supervisor before starting (not training eligible).
- **Sensor dropouts:** p=0.03 per 5-min window over `['fuel_used_l', 'seatbelt_fastened', 'ground_speed_kmh', 'load_factor_pct']`. Sensor dropouts null the affected metric and, for state-critical signals (speed, load factor), put the missing seconds into unknown_s — never zero or false (principle 5).
- **Roster:** every machine class has beginners, intermediates and experts with overlapping experience; new hires only work after their hire date; experience is computed per task date.

## 4. Sensitivity Runs

Sensitivity benchmarks test model stability under scaled operational frictions:
- `sens_0.5`: All environmental and operator effect terms scaled to 50%.
- `sens_1.5`: All environmental and operator effect terms amplified to 150%.

