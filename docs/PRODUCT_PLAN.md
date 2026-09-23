# ShiftMate — Product Plan

**Version:** 1.0 (final for build) · **Date:** 23 September 2026 · **Event:** Caterpillar Hackathon 2026 (Cat Digital India)
**Problem statement:** Smart Operator Assistant for CAT machinery
**Purpose of this document:** the single source of truth for *what* we are building and *how it must behave*. The implementation plan (repo, tasks, hours) is derived from this document. If the implementation plan and this document disagree, this document wins until it is updated.

---

## Table of contents

1. Product summary
2. Problem and evidence
3. Users and personas
4. Product principles (non-negotiable rules)
5. Positioning against existing Caterpillar products
6. Scope: Must / Should / Later / Never
7. Core concept: Shift Ledger, machine states, propagation, follow-up routing
8. Feature specifications (F1–F18)
9. User journeys
10. Screen inventory
11. Controls and voice interaction model
12. Alert catalogue
13. Data and content requirements
14. AI and ML behaviour requirements
15. Non-functional requirements
16. Platform and technology stack
17. Metrics and evaluation
18. Demo plan
19. Risks and mitigations
20. Assumptions and open questions
21. Traceability to the problem statement and briefing
22. Glossary

---

## 1. Product summary

**One line:** ShiftMate is an offline-first, voice-and-buttons companion app for Cat machine operators that connects the day's tasks, realistic finish times, contextual safety, fair usage review, relevant training and shift handover.

**Core promise:** *The operator explains an event once, and the whole shift uses it.*

**What it is**
- An operator-first mobile app for the cab tablet or machine display (Android first).
- Fully usable with no internet, and without touching the screen.
- A small web console for supervisors and trainers.
- A backend that syncs records, runs language AI when online, and trains models.

**What it is not**
- Not a machine controller. It never moves, stops or limits the machine.
- Not a replacement for the machine's own alarms, Cat Detect, Collision Mitigation or site radio.
- Not a manager surveillance dashboard. The operator sees their own data first.
- Not a certification system. Completing a lesson authorises nothing.

**Elevator pitch (30 seconds)**
Cat machines already record hours, fuel, idle, load cycles, seatbelt and alerts, but the operator only sees raw numbers or a beep. ShiftMate turns that data, plus one explanation from the operator, into guidance that is fair and honest. When the operator says "waiting for the truck", the finish time adds waiting, the idle becomes a site delay rather than their fault, no pointless lesson is pushed, and the next operator hears about it in the handover, while safety alerts stay fully independent. Everything important works offline, even 4 km deep in a mine pit.

---

## 2. Problem and evidence

### 2.1 The problem in the operator's words
- "The app tells me I idled 55 minutes. I was waiting for a truck. Why is that my fault?"
- "The planner says 30 minutes. It never takes 30 minutes when it rains."
- "The beep went off. I don't know what it was for, and nobody asked what happened."
- "Training is a video I watched once. It had nothing to do with my machine or my site."
- "The night operator knew about the problem. Nobody told me."

### 2.2 Evidence from the organiser data
| Finding | Numbers | Product consequence |
|---|---|---|
| Safety flags coincide with long idle and unfastened belt | Rows 2 and 4: idle 55 and 60 min, 2 and 1 load cycles, belt unfastened, alert = Yes | Seatbelt and idle must be interpreted together with machine state; data alone can't say whether the operator left the cab |
| Fuel per cycle jumps on those rows | 0.43 and 0.61 L/cycle vs 1.90 and 2.00 L/cycle | Fuel per cycle is a useful usage signal, compared within the same context |
| Readings are irregular | Engine hours +1.3 h over 2 h, +1.7 h over 4 h, +3.7 h over 19 h | Keep original records as they are; never interpolate them |
| Planner estimates ignore conditions | MAE 7.6 min, MAPE 13.2%, planner underestimates by 6 min on average | Estimates must account for skill, weather, machine age and quantity, and show a range |
| Skill and conditions matter | Beginner +40% (T003); rainy intermediate +15.6% (T002); windy intermediate +16.7% (T005); experts −3.3% and −5.7% | New operators need the most help; conditions must change estimates and safety |

### 2.3 The gap
The data is already collected, but it is not turned into timely, fair, explained guidance for the person operating the machine, and the context the operator knows ("why") is never captured in a way that other features can use.

---

## 3. Users and personas

### 3.1 Primary: the machine operator
| Persona | Profile | Main needs | Constraints |
|---|---|---|---|
| **Ravi — new operator** | 3 weeks in; Cat 320-class excavator; construction site near Chennai; Tamil and English; day shift | What's next, how long it should take, what went wrong, learn fast without being blamed | Low confidence; limited reading in English; learns from senior operators |
| **Senthil — experienced operator** | 11 years; Cat 777-class haul truck; open-pit mine; Hindi and English; rotating night shifts | Zero distraction while driving, fair treatment of queue time, fatigue and proximity awareness, clear handover | Works 3–4 km from the site office with no mobile signal |

**Cab conditions for both:** gloves, vibration, glare, dust, heat, noise, night work, hands on controls, eyes on the work. No touch screen (Persona doc). Machine data arrives over the machine's CAN bus.

### 3.2 Secondary users
| User | Uses | Needs |
|---|---|---|
| Next-shift operator | Operator app | A clear handover of open items |
| Site supervisor / dispatcher (2–3 people for ~100 machines) | Web console | Only the items that need action: site delays, machine checks, incident reviews, assignment requests |
| Trainer / instructor | Web console | Review near-misses, approve scenarios, see help requests |
| Safety coordinator | Web console | Incident records with context and review status |
| Mechanic | Web console | Machine-check follow-ups (e.g. belt switch flapping) and resolving defect handover items |

### 3.3 Jobs to be done (operator)
1. Know today's work and what "done" means for each task.
2. Know how long it will really take, and why.
3. Stay safe without looking away from the work.
4. Explain a delay or event once, without filling forms.
5. Learn from real situations, when there is time.
6. Pass on what the next operator needs to know.

---

## 4. Product principles (non-negotiable rules)

1. **Operator first.** Every screen is designed for the person in the cab. Supervisor needs are served by the console, not by adding to the cab screen.
2. **No touch required.** Every operator action works with buttons, a controller or voice. Touch may exist but is never needed.
3. **Explain once.** An operator explanation is captured once and reused by every affected feature.
4. **Say where every fact came from.** Every fact is Observed (sensor), Reported (operator), Inferred (rule or model) or Reviewed (a person), with freshness and confidence.
5. **Unknown stays unknown.** Missing or stale data is shown as unavailable, never as safe or normal.
6. **Safety is independent.** No explanation, acknowledgement or correction can switch off an active hazard.
7. **Acknowledged is not resolved.** Alerts and handover items have separate acknowledge and resolve states.
8. **Coach only when it helps.** Corrective coaching is recommended only for a trainable cause that repeats. Preparation is offered only for work or conditions the operator is about to face and has rarely faced; refreshers only when the operator asked for them. All training is offered only when the machine is secured and the operator chooses it.
9. **Route to the right owner.** Every finding goes to the operator, the site, the machine, or nobody.
10. **The AI never creates numbers.** Numbers and safety states come from rules and models; language AI only interprets and phrases.
11. **Offline first.** Safety, tasks, estimates, records, lessons and core voice work with no internet, ever.
12. **Minimal interruption.** While working, one tile and spoken alerts; questions wait until the machine is idle or secured.
13. **Honest claims.** Prototype results come from simulated data and are labelled as such.
14. **Private learning.** Practice answers and learning history belong to the operator and are not sent to supervisors by default.

---

## 5. Positioning against existing Caterpillar products

| Caterpillar product (public information) | What it does | How ShiftMate relates |
|---|---|---|
| **Product Link** | Telematics hardware sending hours, fuel, idle, location, faults | A future data source through ISO 15143-3 or a CAN gateway; not replaced |
| **VisionLink** | Fleet management; seat belt and overspeed monitoring; video event review for training | Manager-side view; ShiftMate is operator-side and syncs records that could feed it |
| **Cat AI Assistant** | In-cab voice coach "from machine startup to shift handoff"; manuals; machine health; runs on NVIDIA Jetson Thor | Same direction. ShiftMate prototypes a focused layer: explain-once context, fair attribution, deciding when not to coach, near-miss learning, acknowledged handover |
| **Collision Mitigation System** | Detects people and obstacles when reversing; alerts; automatic braking | ShiftMate consumes detection events, adds conditions, time-to-contact and a correctable incident record; never controls the machine |
| **Cat safety guidance** | "Always buckle up when operating"; "use your hydraulic lockout lever" before exiting | Directly shapes the seatbelt logic |
| **Cat productivity guidance** | 50-minute hour (83% job efficiency); bucket fill factor; cycle times | Directly shapes the task-time baseline |

**Positioning statement:** "Product Link collects the data and Cat AI Assistant talks to the operator. ShiftMate prototypes the layer in between: context the operator gives once is carried fairly and honestly through the whole shift, and the app decides who should act, including when nobody needs to."

**Claims we never make:** that Caterpillar lacks these capabilities; certified safety distances; accident reduction, fuel savings or learning improvement from the prototype.

---

## 6. Scope

### 6.1 Must (the hackathon build and demo)
| ID | Capability |
|---|---|
| M1 | Operator app sign-in and machine pairing (PIN; key-fob simulated) |
| M2 | Shift briefing with handover receipt and acknowledgement |
| M3 | Daily task board with task states, blockers and completion criteria |
| M4 | Task time estimation: baseline + learned correction + range + work/wait split + live update + conditional ETA + downstream next-assignment impact preview |
| M5 | Working view (Focus Mode) and Drive Mode driven by machine state |
| M6 | Seatbelt logic using machine state and hydraulic lockout, plus a context-sensitive Safe Exit Guard when belt-off coincides with exit intent |
| M7 | Proximity alerts by zone and time-to-contact, condition-aware, freshness-aware |
| M8 | Alert lifecycle (raised, acknowledged, cleared, reviewed) with grouping |
| M9 | Incident capture: automatic context snapshot + one-sentence or button report + correction |
| M10 | Unusual behaviour: idle classes, reason capture, overspeed, fuel per cycle, repeated alerts, follow-up routing |
| M11 | Training hub: library, micro-lessons, decision scenarios, recommendation with reason, condition prep before a rarely faced condition, spaced refresher questions, defer/resume, history, help request |
| M12 | Near-miss → scenario pipeline (template drafting, trainer approval) |
| M13 | Voice: push-to-talk, offline speech-to-text, ~12 intents in English and Hindi, confirmation for records; full button/controller fallback |
| M14 | Handover authoring: draft, edit, voice note, acknowledgement, carry forward |
| M15 | Offline operation with on-device storage and outbox sync |
| M16 | Machine profiles: Cat 320-class excavator (construction, full) and Cat 777-class haul truck (mining, minimal) |
| M17 | Supervisor/trainer web console: follow-up list, incident review, scenario approval |
| M18 | Organiser data replay and scenario simulator |
| M19 | Evaluation script producing a results file |

### 6.2 Should (if Must is complete)
| ID | Capability |
|---|---|
| S1 | Claude-powered language features (online): free-form incident extraction, handover wording, scenario drafting, free questions |
| S2 | Tamil voice (speech model and intent examples) |
| S3 | Site tips: experienced operators record short tips attached to a task type or area |
| S4 | On-device personalisation of estimates and baselines (see F18) |
| S5 | Emergency SOS over LoRaWAN (simulated gateway in demo) |
| S6 | Fleet status view for 100 simulated machines |
| S7 | IsolationForest secondary usage flag; LightGBM + SHAP estimate comparison |
| S8 | Weather from a forecast feed, cached |
| S9 | Secured-state incident replay with one deterministic counterfactual and a focused training-scenario recommendation, when the existing timeline makes it inexpensive |

### 6.3 Later (designed, stated, not built)
- Real Product Link / VisionLink / ISO 15143-3 integration and CAN/J1939 gateway.
- Full instructor scheduling and dealer training integration.
- Walkaround inspection (Cat Inspect already exists; integrate rather than duplicate).
- On-device small language model.
- Camera-based proximity or fatigue detection.
- Fleet dispatch optimisation.
- Full incident reconstruction or physics simulation beyond the bounded deterministic replay in S9.

### 6.4 Never
- Machine control of any kind.
- Automatic skill certification or authorisation to operate.
- Hidden monitoring of operators; ranking operators by speed.
- Claiming field safety or productivity results from simulated data.

---

## 7. Core concept

### 7.1 Shift Ledger
An append-only record of everything that happens in a shift, stored on the device and synced later.

| Field | Meaning |
|---|---|
| `entry_id` | Unique ID (UUID), also the sync idempotency key |
| `shift_id`, `machine_id`, `operator_id` | Context |
| `kind` | observation, report, inference, alert, incident, task_event, idle_event, handover_item, learning_event, correction |
| `source` | `observed` / `reported` / `inferred` / `reviewed` |
| `payload` | Structured content for the kind |
| `observed_at`, `recorded_at` | Event time and record time |
| `freshness_s` | Age of the underlying signal at use time (observations) |
| `confidence` | high / medium / low (inferences, extracted reports) |
| `rule_or_model_version` | Which rule or model produced it (inferences) |
| `original_text` | The operator's words (reports) |
| `supersedes` | Previous entry ID when this is a correction |
| `audience` | operator_only / next_operator / site / trainer / safety |
| `data_origin` | Where the record came from: live app / demo seed / synthetic generator version + seed / organiser / team-recorded (§13.2) |
| `sync_status` | pending / sent / confirmed / needs_review |

**Rules:** entries are never edited in place; corrections create a new entry that supersedes the old one; the latest non-superseded entry is the current truth; history is always viewable.

### 7.2 Machine states
Derived on the device from machine signals every second.

| State | Definition (defaults; per profile) | Cab UI |
|---|---|---|
| `OFF` | Engine not running | Full app |
| `SECURED` | Engine on, hydraulic lockout engaged (or park brake set for trucks), no motion | Full app except long content needs opt-in |
| `READY` | Engine on, lockout released, no motion, load factor < 20% | Task board, prompts allowed |
| `WORKING` | Implement active or load factor ≥ 20% or load cycles increasing | Focus Mode |
| `TRAVELLING` | Ground speed > 5 km/h | Drive Mode |
| `UNKNOWN` | Required signals missing or older than their freshness limit | Status banner; conservative behaviour |

"Idle" = engine on and in `SECURED` or `READY` for longer than the idle threshold.

### 7.3 Explain-once propagation
When a report or correction is added, the propagation engine re-evaluates only the affected consumers:

| Trigger | Consumers re-evaluated |
|---|---|
| Idle reason reported / corrected | Estimate (waiting vs active), usage review (attribution), training relevance, handover draft, site follow-ups |
| Delay or blocked reason accepted | Current-task ETA, downstream next-assignment impact preview, optional reassignment/supervisor-notification request; task order and assignment remain unchanged |
| Task event (start, pause, block, complete) | Task board, estimate, handover draft |
| Incident report / correction | Incident record, training (scenario candidate), handover, safety follow-up |
| Condition change | Estimate, proximity thresholds, briefing notes, condition prep (F10-R12) |
| Alert raised / cleared | Working view, usage review (repeat patterns), handover |

**Invariant:** propagation never changes an active safety alert's state.

### 7.4 Follow-up routing
Every usage or safety pattern gets exactly one follow-up owner, with a reason.

| Owner | Examples | Result |
|---|---|---|
| Nobody | Required cool-down idle; one-off event | Recorded only |
| Operator | Repeated unexplained idle in comparable conditions; repeated belt alerts while operating; repeated overspeed | Coaching recommendation with reason (private) |
| Site | Reported truck queues; blocked access; near-misses clustered in one zone | Site follow-up item in the console |
| Machine | Possible faulty sensor (belt switch flapping); fuel-per-cycle drift over days | Machine check item in the console |

Routing uses rules first; uncertain cases go to "needs review" rather than to the operator.

---

## 8. Feature specifications

Each feature lists purpose, user stories, requirements, behaviour rules, offline behaviour and acceptance criteria. Requirement IDs (e.g. F4-R3) are referenced by the implementation plan and tests.

---

### F1. Sign-in and machine pairing

**Purpose:** identify the operator and machine quickly, set language and guidance level.

**User stories**
- As an operator, I sign in with a PIN using buttons, so I don't need to type or touch.
- As a new operator, I get more explanations; as an experienced operator, fewer.

**Requirements**
- F1-R1: Sign-in by 4–6 digit PIN via buttons/controller; key-fob sign-in simulated by a button.
- F1-R2: Machine is paired to the tablet (configured once); operator selects nothing to pick the machine.
- F1-R3: Language: English, Hindi (Must), Tamil (Should); remembered per operator.
- F1-R4: Guidance level: Guided (new operator default for first 30 days) or Concise; operator can switch.
- F1-R5: Works offline using the operator list stored on the device.

**Acceptance:** an operator signs in with buttons only in under 15 seconds, and the app opens in their language and guidance level.

---

### F2. Shift briefing and handover receipt

**Purpose:** start the shift knowing what the last operator left and what today looks like.

**Requirements**
- F2-R1: Briefing shows: open handover items, today's tasks summary, site conditions (with age), machine notes (open defects, recent alerts).
- F2-R2: Handover items are read aloud in the operator's language (on request or by default in Guided mode).
- F2-R3: Each open item must be acknowledged (one button for all, or item by item). Acknowledgement does not resolve an item.
- F2-R4: Up to 3 short "today's risk notes" generated by rules from conditions and open items (e.g. "Rain after 14:00: trenches may be slippery; proximity warnings will start earlier").
- F2-R5: Conditions older than 6 hours are shown with their age and marked "old".

**Acceptance:** an incoming operator sees a blocked task and an open defect from the previous shift, acknowledges them, and both remain open.

---

### F3. Daily task board

**Purpose:** show today's work and what "done" means, and let the operator update status with minimal input.

**Requirements**
- F3-R1: Each task shows: type, location/area, quantity and unit, priority, completion criterion, planned time, ShiftMate estimate range, status, blocker (if any), assignment source and revision.
- F3-R2: Task states: `PLANNED`, `ACTIVE`, `PAUSED`, `BLOCKED` (with reason), `COMPLETED`, `CANCELLED`.
- F3-R3: Operator actions by button or voice: start, pause, block (with reason), resume, complete (with confirmation of output), request reassignment.
- F3-R4: Only a supervisor/dispatcher can change assignments; operator requests appear as pending until accepted.
- F3-R5: Completing a task records actual start/end, active minutes, waiting minutes and output.
- F3-R6: Next task is highlighted; "finish by" time for the day is shown.
- F3-R7: Guided mode shows a 3-step preparation card for unfamiliar task types.

**Acceptance:** starting, blocking and completing a task each take one action; completing a task updates the board, the estimate history and the handover draft.

---

### F4. Task time estimation and live finish time

**Purpose:** realistic, explained estimates that separate working time from waiting.

**Estimation method**
1. **Baseline** (Caterpillar production-estimating approach):
   `baseline_minutes = quantity / (rated_rate_per_hour × job_efficiency) × 60`
   - `rated_rate_per_hour` from the machine profile (e.g. bucket capacity × fill factor × cycles per hour for excavators; payload × trips per hour for trucks; metres per hour for trenching).
   - `job_efficiency` default 50/60 (0.83), configurable per site.
2. **Correction:** Ridge regression predicting `log(actual / baseline)` from: operator skill level, experience months, task type, material, weather, visibility, temperature band, machine age, time of day, site congestion.
   `estimate = baseline × exp(prediction)`
3. **Range:** split conformal prediction gives P10–P90.
4. **Waiting:** expected waiting from recent site delay reports for the same task type and site (median of last N), shown separately.
5. **Basis indicator:** `comparable history` / `fallback (baseline only)` / `insufficient data`.

**Requirements**
- F4-R1: Before start, show: active work range (P10–P90), expected waiting, finish time range, basis indicator, and top 2–3 contributing factors ("rain +12%", "experience +18%") labelled as model contributions, not proven causes.
- F4-R2: During the task, progress in the task's unit (loads, tonnes, metres, m²) updates the finish time by blending the prior estimate with the observed rate; the prior's weight falls as progress rises (full observed-rate weight after 30% progress).
- F4-R3: Waiting time (idle with a reported waiting reason) pauses the active clock and adds to waiting, not active time.
- F4-R4: If work is stopped with no known restart time, show a conditional estimate ("about 25 min after work resumes"), never a fabricated clock time or a negative number.
- F4-R5: Keep the original estimate and the actual outcome for every task for review and learning.
- F4-R6: "Why did my estimate change?" (voice or button) explains the change from stored factors.
- F4-R7: The planner's own estimate, when present, is shown next to ShiftMate's for comparison.
- F4-R8: Runs fully on the device (model coefficients shipped in the app).
- F4-R9: When an accepted delay or blocked reason changes the current ETA, immediately recompute the likely effect on the next planned assignment and show both messages, for example: "Current task ETA updated by +18 minutes" and "Task 2 may miss its planned start window."
- F4-R10: The impact preview may offer "Request reassignment" or "Notify supervisor"; these create requests/follow-ups only. ShiftMate never silently reorders tasks or reassigns an operator.
- F4-R11: If the next task has no planned start window or the impact cannot be calculated, show only the current-task change and state that downstream impact is unavailable rather than inventing one.

**Acceptance:** the same task gets different estimates in rain vs dry; a reported truck wait moves the finish time but not active time and previews the next assignment's likely delay; requesting reassignment creates a supervisor decision item without changing task order; progress updates move the estimate again; a new task type shows "fallback".

---

### F5. Working view (Focus Mode) and Drive Mode

**Purpose:** support the operator while working without pulling their eyes off the work.

**Requirements**
- F5-R1: In `WORKING`, the screen shows one tile: current task, progress, finish time, belt status, proximity status, idle timer; max 3 data groups; readable in under 2 seconds.
- F5-R2: In `TRAVELLING`, Drive Mode shows speed vs limit, next stop, proximity status only.
- F5-R3: Menus are locked in `WORKING` and `TRAVELLING`; only acknowledge, push-to-talk and SOS are active.
- F5-R4: Important information is spoken; visual is confirmation.
- F5-R5: Status bar always shows: connectivity (online/offline), records waiting to sync, signal health (sensors fresh / unavailable).
- F5-R6: Night theme and high-contrast theme; colour is always paired with an icon and a word.

**Acceptance:** during simulated work, no prompt requiring a choice appears except safety alerts; the working tile is readable at arm's length.

---

### F6. Safety — seatbelt

**Purpose:** alert when an unfastened belt is actually dangerous, and stay silent when it isn't.

**Rules**
| Machine state | Belt | Response |
|---|---|---|
| `TRAVELLING` | Unfastened | CRITICAL alert, repeated voice until fastened or acknowledged; incident snapshot if > 30 s |
| `WORKING` or `READY` (lockout released) | Unfastened | WARNING alert, voice |
| `SECURED` | Unfastened | No safety alert; if idle continues, idle review may ask the reason |
| `OFF` | Any | Nothing |
| Any | Belt or lockout signal missing/stale | Status "belt monitoring unavailable"; never shows "OK" |

**Safe Exit Guard**
- Exit intent is present only when the belt changes to unfastened and, within 10 seconds, either the seat becomes vacant or the cab door opens. Belt-off alone never triggers the guard.
- If exit intent is present and the machine is not `SECURED` or `OFF`, show a full-screen advisory: lower or neutralize the implement; engage hydraulic lockout or parking brake; confirm machine motion has stopped; exit only after the machine is secured.
- The advisory clears when the machine becomes `SECURED`/`OFF`, the seat is occupied and door closed again, or the operator acknowledges "Not exiting". It never sends a machine-control command and is not a certified interlock.

**Requirements**
- F6-R1: Evaluate rules every second on the device.
- F6-R2: Debounce: condition must hold for 2 consecutive seconds before alerting (avoid switch bounce).
- F6-R3: Per-shift belt compliance summary shown privately to the operator at end of shift.
- F6-R4: A belt switch that flaps repeatedly (e.g. > 10 changes in 5 min while secured) creates a machine-check follow-up, not an operator alert.
- F6-R5: Organiser rows 2 and 4 (belt unfastened + long idle, lockout unknown) are presented as "extended idle with belt unfastened — context needed", compatible with the recorded flags, without claiming the operator left the cab.
- F6-R6: Evaluate Safe Exit Guard inputs every second using fresh belt, seat-occupancy, cab-door, motion, implement-neutral and lockout/parking-brake signals.
- F6-R7: Belt-off without a fresh seat-vacant or door-open signal produces only the existing state-based belt response; it never produces the full-screen exit advisory.
- F6-R8: When exit intent is detected while unsecured, the full-screen advisory is visual and spoken, remains advisory-only, and cannot lower an implement, apply a brake, engage lockout or otherwise control the machine.
- F6-R9: Missing or stale seat/door/security signals must be named as unavailable; ShiftMate must not state that the machine is secured.

**Acceptance:** belt off while digging → spoken warning but no exit advisory; belt off plus door open or seat vacant while unsecured → full-screen Safe Exit Guard; securing the machine clears it; belt off with lockout engaged → no alarm; belt signal removed → "unavailable"; no test causes machine control.

---

### F7. Safety — proximity and working conditions

**Purpose:** warn early about people and vehicles near the machine, adjusted for conditions, and be honest when sensing fails.

**Inputs (simulated in prototype):** detection events with object type (person, light vehicle, heavy vehicle, structure), bearing, distance, closing speed, sensor quality, timestamp.

**Rules**
- Time-to-contact (TTC) = distance ÷ closing speed (only when closing).
- Zones per machine class: excavator swing radius (all around), truck reversing path and forward path.
- Default thresholds (illustrative, per profile): CAUTION if TTC < 6 s or object inside the outer zone; WARNING if TTC < 3 s or inside the inner zone; CRITICAL if a person is inside the inner zone while the machine is moving or swinging.
- Condition modifiers (illustrative, per profile, shown as assumptions): rain × 1.25 zone size, dust × 1.3, darkness × 1.3, combined multiplicatively and capped at 1.6.
- Freshness: detection feed older than 2 s → "proximity monitoring unavailable".

**Requirements**
- F7-R1: Spoken alert names the object and direction ("Person, rear left").
- F7-R2: Moving-away objects do not raise alerts.
- F7-R3: Repeated alerts for the same object are grouped.
- F7-R4: WARNING and CRITICAL alerts automatically create an incident context snapshot.
- F7-R5: Working-condition settings: rain, dust, darkness, heat (break reminder above a heat-index threshold), wind (warnings for lifting and demolition tasks only). All values come from the profile with a provenance note.
- F7-R6: Condition input comes from cached forecast (when available) or the operator's own report ("raining now").

**Acceptance:** the same distance gives different results for an approaching vs departing person; rain makes warnings start earlier; stopping the feed shows "unavailable" within 2 seconds.

---

### F8. Alert lifecycle and incident logging

**Purpose:** alerts that mean something, and incident records that are complete without paperwork.

**Alert lifecycle**
`RAISED → ACKNOWLEDGED → CLEARED (condition gone) → REVIEWED (optional, by a person)`
- Acknowledging stops repeated voice but keeps the hazard visible while the condition is active.
- An alert can be flagged "wrong or annoying" by the operator; this creates a review item and never clears an active hazard.
- Related alerts within 60 s for the same cause are grouped into one.

**Incident logging**
- F8-R1: Automatic context snapshot for WARNING/CRITICAL alerts and on operator request: machine state, speed, location, belt, lockout, proximity events, conditions, active task, for 60 s before and 30 s after.
- F8-R2: Operator report when safe (`SECURED` or `OFF`, or immediately if the operator chooses): one spoken sentence or button choices (type → object → place → contact yes/no).
- F8-R3: Incident types: near miss, contact with person, contact with vehicle/structure, machine fault, unsafe condition, other. Severity: low / medium / high.
- F8-R4: Extracted fields are read back; the operator confirms or corrects. Negation creates nothing ("there was no near miss").
- F8-R5: Each field shows its source: observed (snapshot), reported (operator), inferred (extraction).
- F8-R6: Records are append-only with a hash chain (each record stores the hash of the previous one) so later edits are detectable.
- F8-R7: Incidents are routed to the safety coordinator and trainer queues in the console; near-misses become scenario candidates (F10).
- F8-R8: Offline: record and snapshot saved on the device; free-form text is extracted with on-device rules; if extraction is incomplete, the text is kept and refined online later (S1).
- F8-R9 (Should/Later): After the machine is `SECURED` or `OFF`, the operator or trainer may replay the captured 60-second-before/30-second-after incident timeline. Replay is unavailable in `READY`, `WORKING`, `TRAVELLING` or `UNKNOWN`.
- F8-R10 (Should/Later): Replay may apply one deterministic, clearly labelled counterfactual to the recorded timeline, such as reducing travel speed or stopping two seconds earlier. It is an educational comparison, not a claim of what certainly would have happened.
- F8-R11 (Should/Later): Replay never feeds values back into live alerts, machine state or the safety engine, and never controls the machine.
- F8-R12 (Should/Later): Completing a replay recommends or drafts one focused training scenario tied to the incident; trainer approval remains required before wider publication.

**Acceptance:** a near-miss is captured with context automatically, described in one sentence, read back and confirmed in under 20 seconds; acknowledging an active proximity alert leaves the hazard shown.

---

### F9. Unusual behaviour and idle review

**Purpose:** identify excessive idling and unsafe patterns fairly, and send each finding to the right owner.

**Idle classes**
| Class | Detection | Follow-up |
|---|---|---|
| Required | Inferred: warm-up (cold engine), cool-down (after high load in last 10 min), parked regeneration flag | None |
| Reported | Operator reason: waiting for truck/loader, access blocked, instructed hold, break, other (free text) | Site follow-up for waits/blocks; appears in handover if unresolved |
| Unexplained | No signal-based reason, no report | Ask once; coaching considered only if unexplained idle repeats in comparable conditions |

**Idle prompt behaviour**
- F9-R1: After the profile's idle threshold (default 5 min), ask once: "Why the wait?" with the 4 most likely reasons (learned per operator/site) on buttons 1–4, or voice.
- F9-R2: If unanswered, do not repeat; mark as unexplained; allow answering later from the task board.
- F9-R3: Show engine-off suggestion with estimated fuel and cost when expected wait exceeds 10 min (values from profile; labelled estimate).

**Other patterns**
| Pattern | Detection | Default owner |
|---|---|---|
| Overspeed (trucks) | Speed above zone limit for > 5 s | Operator if repeated; site if limit/signage issue suspected |
| High fuel per load cycle | Robust z-score > 3 vs comparable context (same machine class, task, material) | Operator (technique) / machine (drift over days) — needs review |
| Repeated belt alerts while operating | ≥ 3 in a shift | Operator coaching |
| Belt switch flapping | Many changes while secured | Machine check |
| Near-misses clustered in one zone | ≥ 2 in a zone within 7 days | Site |

**Requirements**
- F9-R4: Every finding shows: what was observed, possible explanations, chosen follow-up owner, reason, and evidence status (reported / corroborated / unresolved / insufficient evidence).
- F9-R5: Comparisons use comparable context only; with too little history, show "insufficient evidence" instead of judging.
- F9-R6: Operator can correct an explanation; all downstream views update; the original stays in history.
- F9-R7: Operator sees their own findings first; only site and machine items go to the console automatically.

**Acceptance:** two equal idles produce different follow-ups because one has a reported truck wait; a required cool-down produces no follow-up; correcting a reason updates estimate, usage review, training and handover consistently.

---

### F10. Training hub

**Purpose:** relevant, practical learning for new and experienced operators, offered at the right time.

**Content types**
| Type | Format | Length |
|---|---|---|
| Micro-lesson | 4–6 illustrated cards with narration audio + 2 check questions | 60–90 s |
| Decision scenario | Situation (text + illustration + audio), 3 choices, explanation for each | 1–2 min |
| Near-miss scenario | Decision scenario generated from a reviewed real near-miss, anonymised | 1–2 min |
| Guided task card | 3 steps before an unfamiliar task (Guided mode) | 15 s |
| Refresher question | One question taken from a lesson or scenario the operator already completed, asked again days later (F10-R13) | 20–30 s |
| Site tip (Should) | 20-second voice tip from an experienced operator, tagged to task type or area | 20 s |

**Requirements**
- F10-R1: Library browsable by machine class, task type and topic; searchable offline.
- F10-R2: Recommendations come from: task preparation (upcoming unfamiliar task), condition preparation (F10-R12), operator request (including refreshers, F10-R13), or a reviewed pattern with a trainable cause. One alert never triggers a recommendation by itself.
- F10-R3: Every recommendation shows its reason ("Suggested because belt came off while digging 3 times this week") and a "not relevant" button; feedback reduces similar suggestions.
- F10-R4: Content is offered only in `SECURED` or `OFF` and only when the operator opts in; it can be deferred and resumed.
- F10-R5: Wrong scenario answers show the explanation and allow another attempt; two failures offer "ask a trainer" (creates a help request in the console).
- F10-R6: History shows completed lessons and scenarios, answers and dates. It is private to the operator by default.
- F10-R7: Completion never changes qualification or authorisation status.
- F10-R8: Site delays, required idle and sensor faults never produce technique lessons.
- F10-R9 (near-miss pipeline): reviewed near-miss → draft scenario (template on the server; Claude drafting when online, S1) → trainer edits and approves in the console → published to all operators of that machine class in the next content sync.
- F10-R10: Launch content pack: at least 6 micro-lessons and 6 decision scenarios for the excavator profile, 3 lessons and 3 scenarios for the haul-truck profile, in English and Hindi.
- F10-R11 (Should/Later): A secured-state incident replay may recommend a focused scenario for the same hazard and machine class; the replay and recommendation retain the source incident ID but published training is anonymised.
- F10-R12 (condition prep): When rain, dust or darkness is active or forecast during the operator's remaining work today, and the operator has worked fewer than 3 tasks in that condition on this machine class, offer one short scenario or lesson for that condition before it arrives (e.g. "Rain after 14:00 — you haven't trenched in rain yet. 60-second scenario: rain starts during trenching."). It applies only in the operator's first 12 months, uses the machine profile's condition-to-content list, is offered at most once per shift, and counts only the operator's own history, which stays private.
- F10-R13 (refreshers): On finishing a lesson or scenario, the operator may choose "Remind me with a quick question". One of its questions then comes back about 2, 7 and 30 days later, parked only and at most once per shift. A correct answer moves to the next gap; a wrong answer shows the explanation and starts again at 2 days. After the 30-day question is answered correctly, refreshers for that item stop. There are no scores, streaks or comparisons.

**Launch content list (excavator)**
Lessons: seatbelt and hydraulic lockout; working near people (swing radius); working in rain and poor visibility; idle and engine-off decisions; loading trucks efficiently; trenching near utilities.
Scenarios: person enters swing radius; truck driver walks behind machine; rain starts during trenching; belt alarm while repositioning; truck queue builds up; utility marker found mid-dig.

**Launch content list (haul truck)**
Lessons: speed on haul roads; light vehicles on haul roads; queue discipline at shovel and crusher.
Scenarios: pickup crossing in dust; overspeed on downhill; queue at crusher with engine running.

**Acceptance:** an event pattern leads to a recommendation with a reason; the operator defers it, later completes a scenario while secured, and finds it in history; a truck wait never triggers a technique lesson; a reviewed near-miss appears as a new scenario after approval; a new operator with no rain history is offered the rain scenario before forecast rain, while an operator with 3 or more rain tasks is not; a completed lesson with refreshers on returns as one question 2 days later, and a wrong answer brings it back after another 2 days.

---

### F11. Voice and controls

**Purpose:** let the operator do everything without touching the screen, in their language, offline.

**Controls**
| Action | Button / key | Controller |
|---|---|---|
| Move between items | Up / Down | D-pad |
| Select / confirm | OK (Enter) | A |
| Back | Back (Esc) | B |
| Acknowledge alert | ACK (Space) | Right bumper |
| Push-to-talk | Hold PTT (V) | Left bumper |
| Quick choices 1–4 | 1–4 | X, Y, triggers |
| SOS | Hold SOS 3 s | Hold Start 3 s |

**Offline voice pipeline**
1. Push-to-talk starts recording.
2. Speech-to-text on the device (Vosk small models; vocabulary biased to domain words).
3. Normalise: lower-case, remove fillers, map synonyms and languages to canonical words ("lorry", "dumper", "gaadi" → `truck`).
4. Intent: deterministic rules first for emergency, cancel, confirm and other high-consequence commands; a fine-tuned multilingual DistilBERT model exported to ONNX handles the remaining English/Hindi intent classification on-device; current machine state and last question narrow the allowed options.
5. Slots: reason, object, place, numbers, contact yes/no.
6. Negation and correction handling ("no", "not", "nahi", "illa"; "actually…").
7. Confidence check: below threshold → offer top 3 options on buttons.
8. Records are read back and confirmed; questions are answered directly.
9. Action updates the Shift Ledger and triggers propagation.

**Intents (launch)**
| Intent | Example (English) | Example (Hindi, romanised) | Result |
|---|---|---|---|
| `NEXT_TASK` | "What's next?" | "agla kaam kya hai" | Reads next task and estimate |
| `START_TASK` | "Start trenching" | "kaam shuru" | Starts selected/next task |
| `PAUSE_TASK` | "Pause" | "ruko" | Pauses active task |
| `COMPLETE_TASK` | "Done, 40 metres" | "kaam ho gaya" | Asks to confirm output, completes |
| `REPORT_DELAY` | "Waiting for the truck" | "truck ka wait kar raha hoon" | Idle reason recorded; propagation |
| `REPORT_BLOCKED` | "Access blocked" | "rasta band hai" | Task blocked with reason |
| `WHY_ESTIMATE` | "Why am I late?" | "late kyun hai" | Explains from stored factors |
| `LOG_INCIDENT` | "Log near miss, worker behind me" | "near miss likho, peeche aadmi tha" | Incident draft, read back, confirm |
| `CANCEL` / negation | "Cancel" / "There was no near miss" | "nahi, kuch nahi hua" | Cancels pending action; creates nothing |
| `CORRECT_LAST` | "Actually, access blocked" | "nahi, rasta band tha" | New version of last report |
| `ADD_TO_HANDOVER` | "Add to handover: east trench soft" | "handover mein likho…" | Handover note |
| `REPEAT_ALERT` | "Repeat" | "phir se bolo" | Repeats last alert |
| `EMERGENCY` | "Emergency" | "emergency" | SOS flow (F14) |

Tamil examples (Should) are added after validation by a native speaker.

**Requirements**
- F11-R1: End-to-end voice command latency ≤ 2 s on a mid-range Android device, offline.
- F11-R2: Every intent has an equivalent button path.
- F11-R3: Unrecognised utterances (with operator permission) are stored to improve the next content update.
- F11-R4: Voice output: pre-recorded clips for all alerts (all launch languages); device text-to-speech for dynamic text.
- F11-R5: The quantized ONNX intent model and tokenizer ship inside the app, run fully offline, and record model version, top intent, confidence and whether rules or the model produced the decision.
- F11-R6: Low confidence, small top-two margin, an intent forbidden in the current machine state, or model-load/inference failure routes to the top-three/button clarification path; it never silently performs a consequential action.

**Acceptance:** all launch intents work offline in English and Hindi on the voice test set; "there was no near miss" creates no record; every intent can also be completed with buttons.

---

### F12. Handover authoring

**Purpose:** nothing important is lost between the 2–3 operators who share a machine.

**Requirements**
- F12-R1: At end of shift, a draft is built from the ledger: unfinished and blocked tasks, open defects, unresolved incidents, reported delays still open, operator notes, site tips.
- F12-R2: The draft shows the intended audience for each item; private learning data is never included.
- F12-R3: Outgoing operator can add, remove (with reason) or edit items and record a 20-second voice note.
- F12-R4: Handover is stored on the device (same tablet serves the next operator even offline) and synced when online.
- F12-R5: Incoming operator acknowledges; items stay open until resolved by an authorised role (supervisor, mechanic) or the task is completed.
- F12-R6: Offline wording uses templates; online wording can be polished by Claude (S1) without changing facts.

**Acceptance:** a blocked task and an open defect survive a shift change; acknowledgement does not resolve them; private practice answers are absent from the handover.

---

### F13. Offline operation, storage and sync

**Purpose:** the app works fully with no internet, including a device that never had internet.

**What ships inside the app**
Machine profiles, rules, task-estimator coefficients, launch content pack (lessons, scenarios, audio), alert voice clips, speech models (English, Hindi; Tamil Should), quantized multilingual DistilBERT ONNX intent model and tokenizer, intent rules and word lists, demo scenarios, organiser data.

**On-device storage:** SQLite for the Shift Ledger, tasks, records, learning progress, outbox and personal baselines.

**Outbox**
| Field | Meaning |
|---|---|
| `entry_id` | UUID, idempotency key |
| `type` | incident, alert_history, idle_reason, correction, task_event, handover, learning_progress, text_for_extraction, machine_summary |
| `payload` | Record content |
| `created_at`, `operator_id`, `machine_id` | Context |
| `status` | pending / sent / confirmed / needs_review |
| `attempts`, `last_attempt_at` | Retry tracking |

**Sync rules**
- F13-R1: When online, send oldest first; server confirms by `entry_id`; duplicates are ignored.
- F13-R2: Conflicts (e.g. supervisor reassigned a task meanwhile) are marked `needs_review` and shown; never silently overwritten.
- F13-R3: Raw per-second signals stay on the device for 72 hours; only summaries (per 5 min) sync.
- F13-R4: Downloads when online: tasks and assignments, handover from other devices, new approved scenarios, model coefficient updates, forecast.
- F13-R5: Status bar shows "Offline — safety and tasks working, assistant limited" and "N records waiting".

**Offline capability table**
| Capability | Offline |
|---|---|
| Task board, estimates, live finish time | Full |
| Seatbelt, proximity, condition alerts | Full |
| Incident capture and report (buttons, voice intents) | Full |
| Idle review and reasons | Full |
| Training hub (downloaded content) | Full |
| Handover on the same device | Full |
| Free-form language features (S1) | Templates only |
| New near-miss scenarios from other operators | After sync |
| Supervisor console updates | After sync |
| Forecast weather | Last cached, with age; operator can report conditions |

**Acceptance:** with the network disabled from install, a full shift can be completed; on reconnect, all records sync once with no duplicates.

---

### F14. Emergency SOS (Should)

**Purpose:** a backup emergency channel where there is no mobile signal. Not the primary life-safety system.

**Requirements**
- F14-R1: Trigger: hold SOS 3 s, controller Start 3 s, or voice "emergency" followed by confirm.
- F14-R2: Sends a compact packet over LoRaWAN (IN865 band): machine short ID, event type, latitude/longitude, time, severity, sequence number; confirmed uplink with retries.
- F14-R3: The gateway forwards to the backend, which raises a console alarm and sends an SMS to configured contacts.
- F14-R4: The screen instructs the operator to also use the site radio; SOS status shows sending / delivered / not confirmed.
- F14-R5: In the prototype the LoRa radio and gateway are simulated; the packet format and flow are real.

**Acceptance:** an SOS from the "pit" appears on the console within seconds in the simulation, with delivery status shown to the operator.

---

### F15. Supervisor and trainer web console

**Purpose:** give the 2–3 people overseeing ~100 machines only what needs action, and let trainers turn near-misses into learning.

**Screens**
| Screen | Content | Actions |
|---|---|---|
| Follow-ups | Site delays, machine checks, safety incidents, help requests, assignment change requests; sorted by priority and age | Assign, resolve, comment |
| Incident review | Incident record with source-tagged fields and context snapshot timeline | Mark reviewed, correct fields, send to trainer |
| Scenario approval | Draft scenario from a near-miss, editable text and choices | Approve, edit, reject |
| Fleet status (Should) | 100 simulated machines: state, open alerts, sync age | Filter; open machine detail |
| Handover view | Latest handover per machine and acknowledgement status | Resolve items |
| SOS alarm (Should) | Active SOS events | Acknowledge, record response |

**Requirements**
- F15-R1: Console never shows operators' private learning answers.
- F15-R2: Role-based access: supervisor, trainer, safety coordinator, mechanic (machine checks and resolving handover items, F12-R5).
- F15-R3: Mouse and keyboard allowed (no-touch rule applies to the cab only).

**Acceptance:** a truck-queue report from the cab appears as a site follow-up; a near-miss can be approved as a scenario and reaches the operator app on next sync.

---

### F16. Machine profiles and sector scaling

**Purpose:** one core, many machines; adding a machine class is configuration, not code.

**Profile contents**
Machine class and models; supported signals and freshness limits; machine-state thresholds; task types with progress units and rated rates; job efficiency default; idle thresholds and reason lists; seatbelt rule variants; proximity zones and thresholds; condition modifiers with provenance notes; speed limits (trucks); alert texts and voice clip IDs; lesson and scenario tags; guided task cards; condition-prep content list (which lesson or scenario prepares for rain, dust or darkness on this machine class).

**Launch profiles**
| Profile | Sector | Depth |
|---|---|---|
| Excavator 20 t (Cat 320-class) | Construction | Full demo story |
| Haul truck 90 t (Cat 777-class) | Mining | Tasks, Drive Mode, overspeed, proximity, idle reasons, 3 lessons, 3 scenarios |
| Wheel loader (Cat 950-class) | Construction/quarry | Profile file only (proves extensibility) |

**Requirements**
- F16-R1: Profiles are versioned; every alert and inference records the profile version.
- F16-R2: A validation command checks profiles for missing fields.
- F16-R3: Switching the paired machine switches the profile with no code change.

**Acceptance:** switching from excavator to haul truck changes tasks, progress units, modes, hazards and lessons without code changes.

---

### F17. Language AI features (online, Should)

**Purpose:** natural language beyond fixed commands when internet is available.

**Uses**
| Use | Input | Output |
|---|---|---|
| Free-form incident extraction | Operator sentence + snapshot facts | Structured incident fields for confirmation |
| Handover wording | Ledger facts | Short clear note (facts unchanged) |
| Near-miss scenario draft | Reviewed incident | Anonymised scenario for trainer approval |
| Free questions | Question + computed facts from tools | Plain-language answer |

**Guardrails**
- Server-side only (Claude API, Haiku 4.5); the app never calls it directly.
- Model receives only computed facts through tools, never raw telemetry.
- Outputs parsed into strict schemas; invalid output → template.
- Fact check: numbers, units, subject, time and negation must match tool results; mismatch → template.
- No machine-operating instructions; no advice that bypasses safety systems.
- Any record creation is read back and confirmed by the operator.
- 2-second timeout → template.

**Acceptance:** with internet, a free-form incident sentence yields correct fields for confirmation; with the API unavailable, the same flow completes with templates.

---

### F18. On-device learning and personalisation (Should)

**Purpose:** the app improves for each operator and site without internet.

| What it learns | How | Effect |
|---|---|---|
| Operator pace | Personal correction offset updated after each completed task, weighted n/(n+10) | Estimates fit the operator |
| Site conditions | Running effect of rain/material at this site | Estimates fit the site |
| Personal baselines | Running median and spread of idle ratio, fuel per cycle, cycles per hour per task type | "Unusual" relative to comparable context |
| Likely idle reasons | Frequency of reasons by site/time | Best 4 options on buttons 1–4 |
| Lesson relevance | Quiz results and "not relevant" feedback | Better recommendations |

**Requirements**
- F18-R1: Task-specific estimate personalisation starts only after at least 3 comparable completed tasks for the same operator, machine class and task type; before that, the shared estimate remains unchanged.
- F18-R2: Every personalised estimate names the task type and evidence count (for example, "Adjusted using your last four trenching tasks") and widens uncertainty when the evidence count is small.
- F18-R3: All updates are explainable and bounded; a personal offset supplements rather than replaces the shared task estimator.
- F18-R4: Personal task history stays private to the operator by default and is not shown in the supervisor console, handover or team comparisons unless the operator explicitly opts in to share a summary.
- F18-R5: The system never labels an operator weak, slow or unsafe and never creates a permanent operator score or rating from personal pace.
- F18-R6: A reset option restores defaults and deletes the operator's device-only personal statistics.

---

## 9. User journeys

### J1. Ravi's day shift — Cat 320 excavator, construction (primary demo)
| Step | Machine state | What happens | Features |
|---|---|---|---|
| 1 | OFF | Signs in with PIN via buttons; Tamil/English | F1 |
| 2 | OFF | Hears handover: "Trench T2 blocked by utility mark; hydraulic temperature high at 02:10"; acknowledges | F2, F12 |
| 3 | SECURED | Task board: trench 40 m in clay, rain after 14:00; estimate 48–58 min active + ~10 min expected waiting; basis: comparable history. Offer: "Rain after 14:00 — you haven't trenched in rain yet. 60-second scenario?" → Later (stays under Recommended) | F3, F4, F10-R12 |
| 4 | WORKING | Focus Mode tile; progress 8/40 m; finish time updating | F5, F4 |
| 5 | WORKING | Belt slips off while digging → "Seatbelt, machine operating" | F6 |
| 6 | READY → idle | Idle 6 min → "Why the wait?" → says "waiting for truck" | F9, F11 |
| 7 | — | Finish time adds waiting; active unchanged; site delay recorded; no lesson; handover gets open item | Propagation |
| 8 | — | Says "actually, access blocked" → all views update, original kept | F9-R6 |
| 9 | WORKING | Rain starts; worker approaches from rear; warning earlier than in dry; snapshot saved | F7, F8 |
| 10 | SECURED | "Log near miss, worker behind me, no contact" → read back → OK | F8, F11 |
| 11 | SECURED (break) | Opts into "Person enters swing radius" scenario; wrong first answer, explanation, correct second | F10 |
| 12 | OFF | Handover draft; adds voice note; saved | F12 |
| 13 | Next shift | Next operator acknowledges; blocked task and near-miss stay open | F2 |

### J2. Senthil's night shift — Cat 777 haul truck, 3–4 km in the pit, no signal
| Step | What happens | Features |
|---|---|---|
| 1 | At the yard (Wi-Fi): sign in, handover, tasks (18 hauls, 1,600 t), sync | F1–F4, F13 |
| 2 | In the pit (offline): Drive Mode; speed 42 on a 35 km/h road → spoken overspeed warning | F5, F9 |
| 3 | Light vehicle in dust → earlier proximity warning; sensor drop → "unavailable" | F7 |
| 4 | Queue at shovel 15 min → "shovel queue" (button 1) → site delay; finish time adds waiting | F9, F4 |
| 5 | Near-collision → snapshot; later "log near miss, pickup crossed Road 3" | F8 |
| 6 | Emergency (if needed) → SOS over LoRaWAN; screen reminds to use radio | F14 |
| 7 | Back at yard → 12 records sync; queue goes to supervisor, near-miss to trainer | F13, F15 |

### J3. New operator's first week
Day 0: tutorial using buttons only, language, Guided mode on. Days 1–5: guided task cards before each new task type; handover tips from experienced operators. Week 2: recommended lessons with reasons, scenarios during breaks; before the first rain and first night shift, a short prep scenario for that condition; lessons finished with "Remind me" come back as one quick question after about 2, 7 and 30 days. Week 3: help request answered by a trainer. After at least three comparable completions, task-specific estimates may privately adapt with an evidence count and wider early uncertainty; no automatic certification or permanent operator rating.

### J4. Trainer turns a near-miss into practice
Machine secured → operator/trainer replays the captured timeline → optionally compares one deterministic "lower speed" or "stop two seconds earlier" counterfactual → incident review in console → focused scenario draft appears → trainer edits choices and explanation → approve → next sync publishes to all excavator operators → operators see it with reason "From a real near-miss on this site".

### J5. Supervisor handles follow-ups
Follow-up list: "Truck queue at Loading Bay 2 — 3 reports, 55 min total today" → reassign a truck → resolve. "Belt switch flapping on EX-07" → create mechanic check.

---

## 10. Screen inventory

### Operator app
| # | Screen | Key content | Allowed states |
|---|---|---|---|
| A1 | Sign-in | PIN pad (button-driven), language | OFF, SECURED |
| A2 | Briefing | Handover items, risk notes, conditions (with age), machine notes | OFF, SECURED, READY |
| A3 | Task board | Task list with estimate ranges, states, blockers, next task | OFF, SECURED, READY |
| A4 | Task detail | Estimate breakdown, factors, basis, planner comparison, progress, guided card | OFF, SECURED, READY |
| A5 | Focus Mode | One tile: task, progress, finish time, belt, proximity, idle | WORKING |
| A6 | Drive Mode | Speed vs limit, next stop, proximity | TRAVELLING |
| A7 | Alert overlay | Icon, word, colour, object and direction, ACK hint | Any |
| A7E | Safe Exit Guard | Full-screen advisory checklist; security signal status; "Not exiting" acknowledgement; never machine control | READY, WORKING, TRAVELLING, UNKNOWN when exit intent is present |
| A8 | Idle prompt | "Why the wait?" with 4 reasons + voice | READY, SECURED |
| A9 | Incident report | Snapshot summary, fields with sources, read-back, confirm/correct | SECURED, OFF (or on demand) |
| A10 | Training hub | Recommended (with reasons, including condition prep and refreshers due), library, history, help | SECURED, OFF |
| A11 | Lesson / scenario player | Cards, audio, choices, explanation | SECURED, OFF |
| A12 | Shift summary | Tasks planned vs actual, active vs waiting, alerts, private belt compliance | OFF |
| A13 | Handover editor | Draft items with audience, voice note, save | OFF |
| A14 | Status and sync | Online/offline, records waiting, sensor health, conflicts | Any |
| A15 | SOS | Hold-to-send, delivery status, radio reminder | Any |
| A16 | Settings | Language, guidance level, personal data reset | OFF |
| A17 | Incident replay (Should/Later) | Recorded timeline, one deterministic counterfactual, training recommendation | SECURED, OFF |

### Web console
| # | Screen |
|---|---|
| C1 | Sign-in with role |
| C2 | Follow-ups |
| C3 | Incident review |
| C4 | Scenario approval |
| C5 | Handover view |
| C6 | Fleet status (Should) |
| C7 | SOS alarm (Should) |

### Visual rules
- Large type (task tile values ≥ 48 px on a 10-inch display); maximum 3 data groups in Focus/Drive Mode.
- Colour + icon + word for every status (colour-blind safe).
- Night theme and high-contrast day theme.
- Every number has its reason one action away.

---

## 11. Controls and voice interaction model
Covered in F11. Additional rules:
- Voice never starts listening without push-to-talk (no always-on microphone).
- Spoken output is short: ≤ 12 words for alerts, ≤ 25 words for answers while operating.
- In `WORKING`/`TRAVELLING`, only safety, `REPORT_DELAY`, `LOG_INCIDENT`, `REPEAT_ALERT`, `EMERGENCY`, `WHY_ESTIMATE` are accepted; others are politely deferred ("I'll show that when you stop").

---

## 12. Alert catalogue (launch)

| ID | Trigger | Level | Voice (English) | Snapshot | Follow-up |
|---|---|---|---|---|---|
| A-BELT-MOVE | Belt unfastened while TRAVELLING | CRITICAL | "Seatbelt. Machine moving." | Yes (> 30 s) | Operator if repeated |
| A-BELT-OPER | Belt unfastened in WORKING/READY | WARNING | "Seatbelt. Machine operating." | No | Operator if ≥ 3/shift |
| A-BELT-UNAV | Belt/lockout signal stale | INFO | "Belt monitoring unavailable." | No | Machine check if persistent |
| A-PROX-CAUT | Object TTC < 6 s or outer zone | CAUTION | "Person, rear left." | No | — |
| A-PROX-WARN | TTC < 3 s or inner zone | WARNING | "Person close, rear left." | Yes | Incident prompt when secured |
| A-PROX-CRIT | Person inside inner zone while moving/swinging | CRITICAL | "Stop. Person in swing area." | Yes | Incident prompt; safety review |
| A-PROX-UNAV | Detection feed stale > 2 s | CAUTION | "Proximity monitoring unavailable." | No | Machine check if persistent |
| A-SPEED | Speed above zone limit > 5 s (trucks) | WARNING | "Speed 42. Limit 35." | No | Operator if repeated; site if many operators |
| A-HEAT | Heat index above threshold with long working time | INFO | "High heat. Consider a water break." | No | — |
| A-WIND | Wind above threshold during lifting/demolition task | CAUTION | "Strong wind. Check load and boom." | No | — |
| A-IDLE-ASK | Idle > threshold, no reason | INFO (prompt) | "Why the wait?" | No | Per reason |
| A-EXIT-UNSEC | Belt off + seat vacant or cab door open while machine not secured | ADVISORY (full-screen) | "Secure the machine before exiting." | No | None; advisory only |
| A-SOS | Operator SOS | CRITICAL | "SOS sent. Also call on radio." | Yes | Console alarm |

---

## 13. Data and content requirements

### 13.1 Entities (product level)
Machine, MachineProfile, Operator, Site, Zone, Shift, Task, TaskEvent, Estimate, DownstreamImpactPreview, Observation, Condition, ProximityEvent, Alert, AlertBudgetMetric, Incident, IncidentReplay, IdleEvent, Report, Correction, Finding, FollowUp, HandoverItem, Lesson, Scenario, LearningEvent, Recommendation, HelpRequest, OutboxEntry, SOSEvent.

### 13.2 Provenance on every record
`data_origin` (organiser / synthetic generator version + seed / demo seed / team-recorded / live app), units, timestamps (event and receipt), missingness flags. `data_origin` says where a record came from; it is separate from the ledger's `source` (observed / reported / inferred / reviewed), which says how a fact is known.

### 13.3 Organiser data
Kept verbatim in its own folder, flagged `organiser`, never modified or interpolated. Replay must flag rows 2 and 4 only.

### 13.4 Generated data (for development and evaluation)
| Dataset | Size |
|---|---|
| Machines (detailed) | 24: 10 excavators, 6 loaders, 8 haul trucks |
| Fleet (status-level) | 100 machines |
| Operators | 48 fictional, varied experience and language |
| Task history | ~2,500 tasks with quantity, unit, material, conditions, planned, actual, active and waiting minutes |
| Observation streams | 1 Hz for scenario episodes; 5-minute summaries for history |
| Conditions | Per site per hour |
| Proximity episodes | Per scenario family |
| Reports, incidents, alerts | Derived from scenarios |
| Voice test set | ~150 text utterances (English, Hindi; Tamil Should) + ~30 team-recorded clips labelled as team recordings |

Generator assumptions (effects of skill, weather, age, material) are published and varied in a sensitivity run.

### 13.5 Scenario pairs (behaviour tests)
1. Same long idle: truck queue vs unexplained vs required cool-down.
2. Same belt unfastened: operating vs secured vs lockout signal missing.
3. Same proximity distance: approaching vs departing; fresh vs stale.
4. Same task: different quantity, material, weather.
5. Same repeated alert: trainable habit vs faulty switch vs site layout.
6. "Log a near miss" vs "there was no near miss"; corrected machine ID; unsupported command; mixed language.
7. Same correct quiz answer with and without a later chance to observe behaviour.
8. One reason corrected: all affected views update; unrelated safety facts unchanged.
9. No progress or unknown restart: uncertainty shown, never negative time.
10. Offline records then reconnect: no duplicates; separately, sensor outage.
11. Same rain forecast: new operator with no rain history vs operator with 3+ rain tasks vs experienced operator (prep offered / not offered / not offered).

Challenge scenarios are authored by a teammate who did not write the rules.

### 13.6 Content packs
Versioned JSON per machine class and language: lessons (cards, images, audio references, questions), scenarios, guided task cards, alert texts, word lists and intent examples. Audio compressed (~32 kbps).

---

## 14. AI and ML behaviour requirements

| Component | Method | Where it runs | Requirement |
|---|---|---|---|
| Machine-state interpreter | Rules | Device | Deterministic, 1 Hz, debounced |
| Safety rules | Zones, TTC, freshness | Device | Deterministic; alert audio ≤ 1 s after trigger |
| Task-time estimator | Baseline + Ridge on log ratio + split conformal | Trained on server; coefficients run on device | Explainable factors; basis indicator |
| Estimate comparison | LightGBM + SHAP (Should) | Server | Reported only; adopted only if clearly better on the same held-out cases |
| Usage review | Rules → robust z vs comparable context → IsolationForest secondary (Should) | Device (rules, z); server (IsolationForest) | "Insufficient evidence" state |
| Training relevance | Cause → tag rules + feedback | Device | Reason shown for every recommendation |
| Speech-to-text | Vosk small models | Device | Offline; domain vocabulary |
| Intent understanding | Consequential-command rules + fine-tuned multilingual DistilBERT, quantized ONNX | Device via ONNX Runtime | English/Hindi and code-switch evaluation; top-3/button fallback when unsure |
| Language AI | Claude Haiku 4.5 with tool use (Should) | Server | Guardrails in F17 |
| Personalisation | Weighted running statistics | Device | Explainable, resettable |

**Model lifecycle:** task estimators are trained on the server and exported as versioned coefficients/JSON; multilingual DistilBERT is fine-tuned on the server, exported and quantized to ONNX with a versioned tokenizer/config, and run on-device through ONNX Runtime. Artifacts ship in the app or arrive through a model update; every estimate and intent inference stores its model version.

**Candidate not adopted:** Laya (421M-parameter typed-decision model) — its own card reports weak zero-shot accuracy and over-confidence; considered only if it beats the intent classifier on our voice test set.

---

## 15. Non-functional requirements

| Area | Requirement |
|---|---|
| Offline | All Must features work with no internet from install |
| Safety latency | Alert audio ≤ 1 s after rule trigger on device |
| UI latency | Screen state change ≤ 300 ms; voice command ≤ 2 s end-to-end offline |
| Startup | Cold start ≤ 5 s on a mid-range Android tablet |
| Storage | App/model size is measured and disclosed; target ≤ 320 MB with English + Hindi and quantized intent ONNX model (≤ 420 MB with Tamil if a speech model becomes available); ledger growth ≤ 20 MB/month per machine |
| Battery and heat | Speech recognition only while push-to-talk is held; no continuous heavy processing |
| Devices | Android 10+ tablets/phones, 3 GB RAM minimum; 10-inch landscape primary; 6-inch portrait supported |
| Accessibility | Colour + icon + word; large targets; night and high-contrast themes; audio for all critical info |
| Localisation | English, Hindi (Must), Tamil (Should); all alert audio pre-recorded per language |
| Reliability | No record lost on crash or power loss (write-ahead SQLite); outbox retries with backoff |
| Sync integrity | Idempotent by entry ID; conflicts surfaced, never overwritten |
| Privacy | Pseudonymous operator IDs; audience on every record; learning private by default; no always-on microphone; voice audio deleted after transcription unless saved |
| Security | Role-based console access; signed API requests from paired devices; hash-chained incident records |
| Auditability | Every inference and alert stores rule/model/profile version |
| Honesty | Illustrative thresholds labelled in profiles and UI; simulated data labelled |

---

## 16. Platform and technology stack

| Layer | Choice |
|---|---|
| Operator app | React Native + Expo (TypeScript); Android first; iOS from the same code; web build for judges |
| On-device storage | SQLite (expo-sqlite) |
| On-device voice | Vosk small models (English, Hindi; Tamil Should); device text-to-speech (expo-speech); pre-recorded alert clips |
| On-device intent | Consequential-command rules + fine-tuned multilingual DistilBERT exported as quantized ONNX; ONNX Runtime on Android; versioned tokenizer/config bundled offline |
| Supervisor/trainer console | React web, Tailwind CSS, Recharts |
| Backend | Python, FastAPI, WebSockets, Pydantic, PostgreSQL |
| ML | PyTorch + Hugging Face Transformers/Optimum for DistilBERT fine-tuning and ONNX export; ONNX Runtime for device intent inference; scikit-learn for Ridge, conformal intervals, robust z and IsolationForest; LightGBM + SHAP (comparison) |
| Language AI | Claude API (Haiku 4.5) with tool use, server-side only |
| Emergency channel | LoRaWAN (IN865) via gateway → network server (e.g. ChirpStack) → backend (simulated in demo) |
| Data generation | Python generator + YAML scenario families |
| Delivery | Docker Compose, pytest, Jest/Vitest, GitHub Actions |
| Production path | Product Link / VisionLink / ISO 15143-3 feed and CAN/J1939 gateway → AWS IoT Core → same backend services |

**How it is sold:** as an app on the machine's cab tablet or display (operator), with a web console for supervisors and trainers.

---

## 17. Metrics and evaluation

### 17.1 Product metrics (for a real pilot)
| Metric | Why |
|---|---|
| Share of idle minutes explained (required + reported) | Fair attribution works |
| Estimate error and range coverage vs planner | Planning improves |
| Time to log an incident | Reporting effort drops |
| Alert budget: alerts/prompts per operating hour, repeated-alert suppression, duplicate alerts prevented, deferred non-critical prompts, critical delivery latency, acknowledgement/resolution | Interruption stays low without delaying safety-critical communication |
| Handover items acknowledged by next operator | Continuity works |
| "Not relevant" rate on recommendations | Training relevance |
| Repeat safety events per 10 shifts after related practice | Learning signal (observational only) |

### 17.2 Prototype evaluation (reported by the evaluation script)
| Question | Metric | Compared with |
|---|---|---|
| Estimates useful? | MAE, MAPE, P10–P90 coverage and width by task type | Task-type average; baseline alone; planner estimate where present — same held-out operators/sites/weeks |
| Safety behaves? | Missed alerts, nuisance alerts, detection delay; "unavailable" within 2 s | Rule variants — on challenge scenarios |
| Alert budget respected? | Alerts per operating hour; repeats suppressed; duplicates prevented; non-critical prompts deferred until READY/SECURED; critical alerts delivered without delay; acknowledgement/resolution rate | Ungrouped/no-deferral variant on identical scenarios |
| Usage review fair? | Correct follow-up owner on paired scenarios; valid waits labelled as waste | Idle-threshold-only rule |
| Training relevant? | Irrelevant recommendations on site-delay/sensor cases; condition-prep offers only to operators new to the forecast condition; refreshers on the 2/7/30-day schedule | Recommend-on-every-alert rule |
| Voice works? | Intent and field accuracy, high-confidence wrong actions, abstention/top-3 rate, negation cases, end-to-end latency, per language and code-switch slice; text and audio separate | Deterministic rules-only path; buttons-only path |
| Propagation consistent? | All affected views updated, no safety change | — |
| Organiser compatibility | Rows 2 and 4 flagged, 1 and 3 not | Recorded flags |
| Operator effort | Inputs per task; prompts per hour | v1 design |

**Not claimed:** field accuracy, accident reduction, fuel savings, lasting learning improvement, certified safety distances.

---

## 18. Demo plan (5 minutes)

| Time | Show | Point made |
|---|---|---|
| 0:00 | Ravi signs in with buttons; handover read aloud; acknowledges | Continuity; acknowledged ≠ resolved |
| 0:30 | Task board: trench 40 m, rain later; range with reasons and basis; "you haven't trenched in rain yet" prep offer → Later | Honest estimates; training prepares before the condition arrives |
| 1:00 | Focus Mode; organiser rows replay → rows 2 and 4 flagged "context needed" | Compatible with organiser data, no overclaim |
| 1:30 | Belt off while digging → alert but no exit advisory; door opens while unsecured → Safe Exit Guard; lockout engaged → advisory clears | Context-sensitive advisory; never machine control |
| 1:50 | "Waiting for the truck" → current ETA +18 min, next task may miss its window, site delay, no lesson, handover — all update; "Notify supervisor" creates a request only | Explain once, downstream impact, human assignment control |
| 2:20 | "Actually, access blocked" → consistent updates, history kept | Corrections |
| 2:40 | Worker approaches in rain → earlier warning; sensor stops → "unavailable" | Honest safety |
| 3:00 | "Log near miss…" → read back → confirmed | One-sentence reporting |
| 3:20 | Trainer approves near-miss as scenario; Ravi practises on break; the rain prep he deferred at 0:30 is still under Recommended with its reason | Shared learning and preparation, only when parked |
| 3:50 | Network off → everything core still works; status shows offline | Offline first |
| 4:10 | Handover saved; next operator acknowledges | Continuity |
| 4:30 | Switch to haul truck: Drive Mode, overspeed, queue reason | Same core, other sector |
| 4:45 | Results file: estimate errors vs baselines, safety scenarios, voice accuracy | Evidence |

Backup: recorded video and seeded offline replay mode.

---

## 19. Risks and mitigations

| Risk | Mitigation |
|---|---|
| React Native setup or device issues | Expo managed workflow; web build as fallback; test on one physical Android device from hour 1 |
| Voice fails in a noisy room | Every intent has a button path; demo uses buttons if voice misbehaves |
| Offline speech/intent accuracy for Hindi or code-switching | Domain vocabulary biasing in Vosk; multilingual DistilBERT evaluated on English, Hindi, Romanised Hindi and mixed utterances; top-3/button fallback; Tamil is Should |
| DistilBERT ONNX exceeds device latency, RAM or APK budget | Quantize and benchmark on the target Android device from the first model build; deterministic rules and buttons remain the safe fallback; disclose measured footprint |
| Model looks circular on synthetic data | Published generator assumptions; independent challenge cases; same-case baselines; honest claims |
| Scope too large | Must list only until checkpoint; freeze at hour 18 |
| Alert fatigue | Alert-budget quality gate, grouping, debounce, repeated-alert suppression, deferral of non-critical prompts while operating, and operator "wrong alert" feedback |
| Operators feel watched | Own data first; private learning; fair attribution; no speed ranking |
| Claude unavailable | All flows complete with templates |
| LoRaWAN hardware unavailable | Simulated gateway with real packet format |
| Judges question novelty vs Cat AI Assistant | Bounded claim; demonstrate explain-once and "not coaching" behaviours |

---

## 20. Assumptions and open questions

**Assumptions**
- Hydraulic lockout, belt, speed, load factor and proximity detection signals are available (simulated in the prototype).
- Seat occupancy, cab-door, implement-neutral, park-brake/motion and lockout signals used by the Safe Exit Guard are available or explicitly shown as unavailable (simulated in the prototype).
- Each machine is shared by 2–3 operators across shifts; 2–3 supervisors oversee ~100 machines.
- "No touch screen" applies to the cab; the console may use a mouse.
- Synthetic data is acceptable when calibrated, labelled and documented.
- "Fuel Used (L)" is litres per reporting interval; "Load Cycles" counts completed loads.
- A tablet is mounted in the cab or the machine display can run an Android app.

**Open questions**
1. Which signals can a real cab device read from the machine (CAN access, Product Link, ISO 15143-3)?
2. Site policy on engine-off during waits, and on idle thresholds.
3. Who resolves handover items at a real site (supervisor, mechanic)?
4. Which languages matter most across Cat India sites?
5. Can near-miss scenarios be shared across customer sites, or only within one site?

---

## 21. Traceability

### Problem statement expected outcomes
| Outcome | Features | Demo time |
|---|---|---|
| Daily task dashboard | F2, F3, F4 | 0:00–0:30 |
| Safety features (seatbelt, Safe Exit Guard, proximity, incident logging, working conditions, alert budget) | F6, F7, F8, §17 | 1:30, 2:40, 3:00 |
| Operator training hub (creative format) | F8/F10 (lessons, decision scenarios, condition prep, spaced refreshers, incident replay/counterfactual Should, near-miss scenarios, help request) | 0:30, 3:20 |
| Unusual behaviour (idling, unsafe patterns) | F9 | 1:00, 1:50, 4:30 |
| Task time estimation (past data + conditions + downstream impact + private task-specific baseline) | F4, F18 | 0:30, 1:50 |

### Briefing and Persona constraints
| Constraint | Where met |
|---|---|
| Operator-facing interface; operator point of view | Principles 1–2, F5, F11 |
| ~100 machines, 2–3 operators | F12, F15, fleet simulator |
| New operator learns quickly | F1 Guided mode, F10, J3 |
| Clean, structured dataset | §13 |
| Standalone software | Adapters; no machine dependency; simulator |
| Organised GitHub repo | Implementation plan (derived) |
| Scalable across portfolio; 1–2 sectors shown | F16 |
| No touch screen | Principle 2, F11 |
| CAN / ISO 15143-3 fields | §13, production path in §16 |
| Caterpillar reference stack | §16 |

---

## 22. Glossary

| Term | Meaning |
|---|---|
| Shift Ledger | Append-only record of all shift facts with source tags |
| Observed / Reported / Inferred / Reviewed | Source of a fact: sensor / operator / rule or model / a person |
| Propagation | Re-evaluating affected features when a new fact or correction arrives |
| Follow-up owner | Who should act on a finding: operator, site, machine or nobody |
| Machine state | OFF, SECURED, READY, WORKING, TRAVELLING, UNKNOWN |
| Hydraulic lockout | Lever that disables hydraulic controls; used before leaving the seat |
| TTC | Time-to-contact: distance ÷ closing speed |
| Freshness | Age of a signal; stale signals mean "unavailable" |
| Baseline estimate | Quantity ÷ (rated rate × job efficiency) |
| Job efficiency | Productive minutes per hour (default 50/60) |
| Conformal interval | Prediction range with measured coverage |
| Outbox | On-device queue of records waiting to sync |
| Profile | Configuration for a machine class |
| Near-miss scenario | Practice question built from a reviewed real near-miss |
| Guided mode | Extra explanation for new operators |
| Condition prep | A short scenario or lesson offered before a condition (rain, dust, darkness) the operator has rarely worked in |
| Refresher | One question from a completed lesson or scenario, asked again after about 2, 7 and 30 days if the operator asked for it |
| SOS | Emergency message, sent over LoRaWAN when there is no mobile signal |
