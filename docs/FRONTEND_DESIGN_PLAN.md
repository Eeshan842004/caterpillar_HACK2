# ShiftMate frontend design plan

**Status:** design direction ready for visual proof · 24 September 2026  
**Applies to:** operator app A0–A17 and console C1–C7  
**Product sources:** `PRODUCT_PLAN.md`, `TECHNICAL_SPEC.md`, `FRONTEND_PLAN.md`

## 1. Design brief

ShiftMate is a cab instrument and shift-continuity tool for heavy-equipment operators. It is not a consumer productivity app, a fleet analytics landing page or a generic SaaS dashboard. The operator may be in glare, dust, vibration or darkness, may be wearing gloves, and must be able to read the active state in about two seconds without touching the display. The supervisor console serves a different job: triaging evidence-backed follow-ups across many machines without turning operators into scores.

The visual character is **quiet field instrument**:

- calm and sparse during normal work;
- unmistakable when a real hazard is active;
- built around stable positions rather than floating cards;
- explicit about source, freshness and uncertainty;
- recognisably connected to machinery and shift work without fake metal, hazard stripes or “rugged” decoration.

The interface should feel designed for this product even with the logo removed.

## 2. Existing design audit

### Preserve

- Large cab type and 64 dp minimum focusable rows.
- Fixed top status and bottom action areas.
- Day/night modes and high contrast.
- Colour paired with an icon and a word.
- Machine-state navigation locks and deferred prompts.
- At most three information groups in Focus and Drive modes.
- Restrained motion; no animation carries safety meaning.
- No-touch keyboard/controller paths and visible focus.

### Replace or refine

| Current pattern | Problem | Required change |
|---|---|---|
| Rounded grey containers at nearly every level | Produces the interchangeable SaaS-card look and weakens hierarchy | Use stable rails, ruled groups and flat work surfaces; reserve radius for controls and overlays |
| `StatusPill` for state, metadata and safety alike | Creates pill soup and makes important states visually equivalent | Keep compact flags only for live state/safety; render metadata in aligned text columns |
| Emoji and Unicode symbols | Looks provisional, varies by platform and does not form a coherent icon family | Build the SVG icon set already required by the technical specification |
| Uppercase section labels such as `TASK`, `FINISH`, `SAFETY` | Generic generated-dashboard tell; slower to scan in repeated use | Use sentence case: “Current task”, “Expected finish”, “Safety” |
| Middle-dot metadata strings | Compresses unlike facts into decorative text and is difficult to scan | Give machine, place, quantity, state and source their own aligned positions |
| System font for every role | Safe but anonymous; large numbers and prose have no distinct voice | Use an offline display/numeric face plus a highly legible multilingual UI face |
| One focus treatment for every surface | A list row, prompt choice and critical action should not have identical emphasis | Keep one focus colour but vary structure by control type; always retain the non-colour marker |
| Hard-coded inline screen layouts | Encourages local card styling and inconsistent spacing | Introduce a small set of named layout primitives before adding more screens |
| Current exact palette chosen only for contrast | Functional but not yet a recognisable visual identity | Prototype the subject-specific palette below, then update the technical tokens only after contrast/device review |

The current implementation already avoids gradients, decorative shadows and gratuitous motion. Those constraints remain.

## 3. Direction development and self-critique

### First idea: rugged cockpit

An obvious direction would use black panels, bright yellow, condensed type, metal textures, chamfered cards and hazard-strip decoration.

### Why that is rejected

That treatment turns the industry into a costume. It competes with real warnings, makes every screen loud, and replaces one template with another. It also risks appearing to imitate Caterpillar branding rather than creating a ShiftMate system.

### Revised direction: quiet field instrument

Use matte, flat surfaces; stable instrument rails; one restrained machinery-yellow accent; disciplined typography; and strong spatial grouping. The memorable element is the **continuity rail**, not surface decoration.

The continuity rail is a structural line used only where information moves across time:

- briefing: previous shift → acknowledged context;
- task board: current task → downstream next assignment;
- incident: before → event → after;
- handover: open now → carried to next shift;
- console: report → evidence → owner → resolution.

It never appears as an ornamental line on every screen. Focus Mode, Drive Mode and full-screen safety states remain pure instruments.

## 4. Visual system

### 4.1 Core palette

The six base colours are deliberately tied to a cab display and work order rather than a lifestyle palette:

| Token | Hex | Use |
|---|---|---|
| Cab black | `#080A0B` | Night background and maximum-contrast text |
| Graphite steel | `#232B30` | Night surfaces, fixed rails and console navigation |
| Work face | `#F4F6F5` | Day canvas; a cool neutral, not cream |
| Instrument white | `#FFFFFF` | Raised work surfaces and text on dark fields |
| Signal yellow | `#FFC400` | Continuity rail, next-work marker and physical-control focus; never decorative fill |
| Instrument blue | `#005EA8` | Keyboard focus, information and links/actions where yellow would imply caution |

Safety remains semantic and independent of brand colour:

| State | Background | Foreground | Shape cue |
|---|---|---|---|
| Safe | `#16723A` | white | check in circle |
| Information | `#1D5E91` | white | information circle |
| Caution | `#FFC400` | cab black | triangle |
| Warning | `#C84D00` | white | warning diamond |
| Critical | `#A50F26` | white | stop octagon |
| Unavailable | `#59636A` | white | crossed sensor |

All final token pairs must pass the existing 4.5:1 contrast check. Critical information must still work in monochrome through icon, word, position and border treatment.

Day mode uses work face as the canvas, instrument white only for active work surfaces, and graphite for fixed rails. Night mode uses true cab black behind graphite surfaces; it does not invert every area into a glowing card. Signal yellow is limited to the continuity rail, current/next marker and selected physical action.

### 4.2 Typography

Use two clearly differentiated, offline-bundled roles:

- **Barlow Semi Condensed:** machine IDs, large readings, times, quantities, speed and short instrument headings. Its narrower construction suits limited cab width without resorting to tiny type.
- **Noto Sans with Devanagari and Tamil subsets:** body copy, actions, explanations, Hindi and Tamil. It prioritises legibility and consistent multilingual metrics.

If device benchmarking shows the bundled fonts violate startup or APK limits, keep Noto Sans for all text and use width, weight and tabular numerals—not a third font—to retain hierarchy.

Rules:

- Sentence case for interface labels. Uppercase is limited to `STOP`, standard abbreviations and machine IDs.
- Tabular numerals for clocks, speed, quantities, ranges and countdowns.
- Body line length: 45–72 characters in the cab, no more than 80 in the console.
- Large values do not receive a decorative eyebrow. The adjacent plain-language label must explain the value.
- Hindi and Tamil layouts are tested with real strings before a screen is accepted; Latin-width placeholders are not sufficient.

Proposed scale, retaining the technical specification's safety floor:

| Role | Cab size / line height | Weight | Typical use |
|---|---|---|---|
| Instrument XL | 96 / 96 | 700 | Drive speed only |
| Instrument L | 64 / 68 | 700 | Finish time, critical countdown |
| Value | 48 / 52 | 650–700 | Progress, task quantity |
| Screen title | 32 / 38 | 600 | One per screen |
| Section | 24 / 30 | 600 | Plain sentence-case group title |
| Body | 20 / 28 | 400 | Cab instructions and content |
| Action | 18 / 24 | 600 | Key/action rail |
| Metadata | 16 / 22 | 450 | Freshness, source, version; never critical content |

### 4.3 Geometry and elevation

- Structural rails, alert banners and main panels: square corners.
- Focusable rows and physical-key controls: 4 dp radius.
- Prompt sheets and modal work surfaces: 8 dp radius.
- Status/source flags: 2 dp radius; no capsule treatment unless the value is genuinely compact and transient.
- No shadows in the cab. Separation comes from surface contrast, spacing and rules.
- Console drawers may use one restrained shadow only when overlaying another work surface.
- No gradients, glass effects, faux metal, carbon fibre, rivets, diagonal hazard tape or decorative grid backgrounds.
- A border must communicate focus, separation, status or chronology. Decorative outlines are removed.

### 4.4 Iconography

Create the technical specification's SVG icon set as one family at 24, 32 and 48 dp. Use a 2.25 dp stroke with squared terminals for normal icons and a solid version for critical/stop states. Icons must not rely on platform emoji rendering.

Required first set:

- machine state: engine, lock, motion, unknown;
- safety: belt, person, pickup, truck, structure, sensor-off, warning, stop;
- environment: rain, dust, darkness, heat, wind;
- system: offline, sync, microphone, speaker, clock;
- workflow: task, flag, handover, book, incident, reviewed, SOS.

Each icon is reviewed at actual cab size in day and night modes. No icon is introduced solely to decorate a heading.

### 4.5 Motion

- No page-load choreography and no repeated fade-and-slide entrances.
- User-triggered sheets/drawers may use a 120–150 ms opacity or direct-position transition.
- Alert appearance is immediate; no easing delays safety information.
- Progress changes update without celebration, bounce or confetti.
- Respect reduced-motion settings on web and Android.

### 4.6 Interface language

- Plain, active, sentence-case copy.
- One term per action across the whole flow: “Acknowledge”, “Resolve”, “Publish”, “Save handover”.
- Acknowledgement and resolution are never synonyms.
- Buttons describe the result: “Notify supervisor”, not “Send”; “Save handover”, not “Submit”.
- Errors name the failed thing and the next action. They do not apologise.
- Empty states give a next step: “No conditions received. Press 3 to report conditions.”
- Do not use promotional copy, clever slogans or conversational filler inside work screens.
- Replace strings such as `EX-07 · Excavator · Chennai` with positioned fields, not a different separator.

## 5. Layout system

### 5.1 Operator shell

The operator shell has three stable zones. Their positions do not change between screens:

```text
┌──────────────── machine and system rail ──────────────────────────┐
│ Offline   3 waiting   Sensors clear   Secured   EX-07   14:18 Ravi │
├──────────────┬─────────────────────────────────────────────────────┤
│ continuity   │                                                     │
│ rail when    │                 active work surface                 │
│ time matters │                                                     │
├──────────────┴─────────────────────────────────────────────────────┤
│ [1] Primary action   [2] Secondary   [ACK] Acknowledge   [M] Menu  │
└──────────────────── physical action rail ─────────────────────────┘
```

Alignment:

- Content and prose are left aligned.
- Large numeric readings align on their decimal/unit edge.
- The status rail uses fixed slots so state changes do not move unrelated information.
- The bottom rail renders discrete key/action pairs instead of a sentence joined by dots.
- Landscape content stops at 1280 dp. Portrait collapses detail into routes, not squeezed columns.

### 5.2 Continuity rail

The rail is 8–12 dp wide with labelled stops only when a real sequence exists. Labels use actual states such as “Previous shift”, “Current task” and “Next task”; never `01`, `02`, `03`.

Yellow means current or next attention, not warning. Safety colours remain reserved for safety semantics. If a warning intersects the rail, the safety banner visually supersedes it.

### 5.3 Console shell

The console is a triage workspace, not a grid of KPI cards:

```text
┌ site / role / connection ──────────────────────────────────────────┐
├──────────────┬──────────────────────────────┬───────────────────────┤
│ Follow-ups   │ Priority queue or evidence   │ Selected item         │
│ Incidents    │ table                        │ chronology, owner,     │
│ Scenarios    │                              │ actions and comments   │
│ Handovers    │                              │                       │
└──────────────┴──────────────────────────────┴───────────────────────┘
```

- The first authenticated view is the actionable queue, not a welcome hero or metric-card row.
- Tables and chronology carry the density. Summary numbers appear only when they change a decision.
- Use a persistent selected-item drawer/detail column instead of opening a card modal for every action.
- Operator identity is subordinate to machine/site evidence; no rankings or performance leaderboards appear.

## 6. Screen-by-screen design intent

### A0–A1: setup and sign-in

- Lead with machine identity: machine ID, class and site occupy a fixed identity band.
- Use a flat operator roster and a distinct PIN instrument, not two floating cards.
- PIN dots, lockout countdown and key-fob simulation have reserved positions to prevent layout jumps.
- Language is a labelled action in the physical action rail.

### A2: briefing

- Use the continuity rail to connect open items from the previous shift to today's work.
- Handover items are ruled rows with source, audience and acknowledgement in consistent columns.
- Risk notes are not warning-coloured unless they meet alert semantics.
- “Acknowledge all” remains visually separate from “Continue to tasks”.

### A3–A4: task board and task detail

- Landscape: 60% dispatch list, 40% selected detail, as specified.
- Task rows use aligned fields rather than cards: sequence, work, location, quantity, estimate, state.
- A yellow left marker identifies the next assignment. It does not fill the entire row.
- The downstream impact occupies the continuity space between current and next task, making cause and consequence spatially explicit.
- The primary estimate is one reading; factors, basis, waiting and planner comparison form a ruled explanation below it.

### A5: Focus Mode

Focus Mode is the strongest expression of the design and contains no menu chrome or card grid:

```text
┌ Current task ─────────────────────────────── 8 / 40 m ─────────────┐
│ Trench T2, east section       ━━━━━━━━━━━━━━━╺                      │
├───────────────────────────────┬────────────────────────────────────┤
│ Expected finish               │ Safety                             │
│ 14:18                         │ Belt fastened                      │
│ 14:10–14:25                   │ Proximity clear                    │
└───────────────────────────────┴────────────────────────────────────┘
```

- The task/progress rail spans the screen; the finish reading is the single dominant element.
- Safety has a stable location and does not become a collection of floating pills.
- Source and range remain visible but subordinate.
- UNKNOWN adds a direct banner without recolouring the whole view.

### A6: Drive Mode

- Speed is the only instrument-XL value.
- Limit sits beside the speed on the same baseline; “Over limit” appears as text and shape, not colour alone.
- Next stop and proximity use fixed lower zones.
- Normal Drive Mode is visually quiet. Only an active hazard takes over the top banner.

### A7–A8 and A7E: alerts, prompts and Safe Exit Guard

- Warning and critical alerts are square, full-width annunciator banners with purpose-built icons.
- Acknowledgement text remains visible while the hazard remains active.
- Prompt option numbers are justified because they map directly to physical keys 1–4.
- Safe Exit Guard uses one full-screen checklist with confirmed/not yet/unavailable aligned in a right column.
- No pulsing borders or repeated animation. SOS hold progress is the only circular countdown treatment.

### A9 and A17: incident capture and replay

- Place the recorded timeline on the continuity rail: before, event, after.
- Source marks sit next to each field; they are square labels with full words, not coloured pill clusters.
- Editing creates a visible correction row; it never visually overwrites the earlier statement.
- Replay uses two aligned traces, original and labelled counterfactual, rather than generic before/after cards.

### A10–A11: training

- Do not imitate a streaming-service or course marketplace card grid.
- Recommended items are a short reading list with duration, reason and availability state.
- The player gives the illustration one clear stage; text and choices remain on a stable reading plane.
- History reads like a private log. No streaks, scores, trophies or celebratory gradients.

### A12, A13, A14 and A16: summary, handover, status and settings

- Shift summary is a work ledger: planned, estimated, active and waiting columns align across tasks.
- Handover reuses the continuity rail and shows exactly what will move to the next operator.
- Status is intentionally diagnostic and dense; unavailable/rejected/conflict rows rise to the top.
- Settings use plain rows and direct descriptions. Destructive reset has a separate confirmation surface.

### A15: SOS

- The hold state is visually distinct from a sent state.
- After sending, delivery state and “Also call on radio” remain fixed and readable.
- Critical red is reserved for this and real critical hazards, never brand emphasis.

### C1–C7: console

- C1 is a restrained sign-in surface using site and role identity, without marketing content.
- C2 is a priority-and-age queue with an evidence detail pane; it is not a dashboard of totals.
- C3 gives the incident timeline and source tags the primary area.
- C4 is an editing workspace: source incident on the left, scenario draft in the centre, preview/explanation on the right.
- C5 is organised by machine and open item; acknowledgement and resolution occupy different columns.
- C6 uses a dense fleet table first. A map or diagram is added only if it improves location decisions.
- C7 uses a persistent critical alarm band and a chronological response log.

## 7. Component architecture

Build layout semantics before screen-specific styling.

### Operator primitives

- `MachineRail`: fixed system and machine slots.
- `ActionRail`: discrete key/action pairs and current feedback.
- `WorkSurface`: flat main content plane with responsive column modes.
- `ContinuityRail`: previous/current/next or before/event/after sequences.
- `InstrumentValue`: tabular value, unit, range and explanatory label.
- `StateFlag`: only live state/safety, with icon + word + optional detail.
- `SourceMark`: observed/reported/inferred/reviewed with word and source colour.
- `FocusRow`: predictable no-touch focus with control-specific layout.
- `RuledGroup`: related rows separated by rules rather than cards.
- `Annunciator`: information/caution/warning/critical banner hierarchy.
- `ChoiceSheet`: up to four hardware-mapped choices.
- `EmptyState`, `ErrorState`, `UnavailableState`: direct next-step copy.

### Console primitives

- `ConsoleShell`, `QueueTable`, `EvidenceDrawer`, `Chronology`, `OwnerState`, `SourceMark`, `ActionGroup` and `EmptyState`.
- Reuse semantic tokens and source/status logic with the operator app, but not cab dimensions or oversized type.

Avoid a generic `Card` primitive. If a component cannot state its information role, it should probably be a layout group rather than a reusable visual box.

## 8. Delivery plan

### D0 — audit and baseline

**Output:** current-screen screenshot set, design inventory and decision log.

- Restore/install local frontend dependencies only when implementation is authorised.
- Capture A1, A2, A3, A5, A6, A7E and A14 at 1280×800 and 393×852 in day/night where applicable.
- Catalogue every radius, status treatment, icon, text style, middle-dot string and one-off layout.
- Record the current two-second readability and keyboard-focus failures.

**Gate:** baseline screenshots and inventory are attached to the implementation task. No visual refactor starts without them.

### D1 — visual proof before system refactor

**Output:** coded or high-fidelity proofs for A2, A3, A5, A7E and C2.

- A5 proves the quiet instrument hierarchy.
- A2/A3 prove the continuity rail and information density.
- A7E proves safety override clarity.
- C2 proves the console is a triage workspace rather than a SaaS dashboard.
- Test day, night, normal, unavailable and warning states with real seed content.

**Self-review questions:**

1. Would the screens still be recognisably ShiftMate without the name?
2. Is yellow carrying current/next attention rather than decoration?
3. Does any surface resemble a generic rounded-card dashboard?
4. Are machine, task, source, state and action visually distinct without colour?
5. Is there one memorable device—the continuity rail—rather than several competing motifs?

**Gate:** choose the revised proof, remove at least one unnecessary visual device, then update the exact palette/font clauses in `TECHNICAL_SPEC.md` before production implementation.

### D2 — foundation implementation

**Output:** tokens, bundled fonts, SVG icons, primitives and a presenter-only design lab.

- Replace Unicode/emoji icons.
- Introduce purpose-based geometry tokens and semantic surfaces.
- Implement type roles with multilingual fallback and tabular numerals.
- Build the operator and console primitives listed above.
- Add a design-lab surface covering every status, source, focus, error, empty and unavailable state.
- Extend contrast/content checks to the revised tokens and missing icon/text keys.

**Gate:** every primitive passes keyboard focus, day/night, 200% web zoom, large Android font and reduced-motion checks.

### D3 — refactor the built Slice 1 screens

**Output:** A0–A8/A7E and shared shell migrated without changing engine behaviour.

- Migrate the shell first, then sign-in/briefing/tasks, then Focus/Drive, then overlays.
- Remove uppercase decorative labels, middle-dot metadata and non-semantic pills.
- Keep existing keyboard paths and test IDs stable where possible.
- Add screenshot checks for normal, alert, stale-signal and Safe Exit states.

**Gate:** all existing Slice 1 functional tests remain green; screenshot review finds no generic card-grid, emoji or clipped localisation regressions.

### D4 — apply the system as new operator screens land

**Output:** A9–A17 built from the approved primitives during product Slices 2–7.

- Incident and handover use the continuity pattern.
- Training uses the reading/player pattern rather than marketplace cards.
- Summary and status use ledger/diagnostic patterns.
- SOS and replay receive dedicated state reviews before acceptance.

**Gate:** a new screen cannot introduce a new colour, radius, shadow, text style or control pattern without a recorded reason.

### D5 — build the console system

**Output:** C1–C7 using queue, evidence, chronology and editing-workspace patterns.

- Build C1/C2 with product Slice 2, C3 with Slice 3, C4/C5 with Slice 4 and C6/C7 only if their Should work is approved.
- Keep the operator's private-learning boundary visible in empty and permission-denied states.
- Test dense 100-machine and long-incident cases, not only ideal demo rows.

**Gate:** supervisors can identify the highest-priority actionable item, its evidence and its owner without opening more than one detail surface.

### D6 — visual and interaction quality gate

**Output:** approved screenshot matrix and recorded device results.

- Review at 1280×800 landscape, 1024×600 compact landscape and 393×852 portrait.
- Review day/night, English/Hindi, normal/empty/error/offline/unavailable/critical states.
- Run contrast, keyboard/controller, reduced-motion, 200% zoom and Android large-text checks.
- Measure cold start and font impact; subset fonts if needed.
- Photograph or record the physical tablet in cab-like glare and low light.
- Conduct a two-second glance test for Focus/Drive and a five-second triage test for C2.
- Remove one nonessential visual element in the final critique pass.

**Gate:** no unresolved critical visual defect, no clipped critical content, no colour-only state and no unreviewed fallback state enters the release build.

## 9. Integration with product slices

| Product slice | Required design work |
|---|---|
| Slice 1 maintenance | D0–D3 refactor of the existing operator surface |
| Slice 2 | A14 diagnostics, pairing states, C1/C2 queue shell and sync failures |
| Slice 3 | Incident chronology, findings, shift ledger and C3 evidence review |
| Slice 4 | Voice feedback, handover continuity, training player and C4/C5 editing patterns |
| Slice 5 | Assignment conflicts, compact/portrait layouts and haul-truck Drive Mode |
| Slice 6 | Estimate explanations, organiser provenance and evaluation-result presentation |
| Slice 7 | SOS, personalisation, forecast, Tamil and replay only after the Must gate |
| Slice 8 | D6 screenshot/device/rehearsal gate |

Design work is not a final polish phase. D1 and D2 precede broad screen implementation; each later slice uses the approved system as it is built.

## 10. Acceptance checklist: no generic generated UI

A screen fails design review if any answer below is “yes” without a product-specific reason:

- Is content chopped into interchangeable rounded cards?
- Are status pills being used for ordinary metadata?
- Are emoji or platform-dependent glyphs standing in for interface icons?
- Are section labels uppercase by habit?
- Are unrelated facts joined with middle dots or spaced dashes?
- Is a monospace font being used merely to make metadata look technical?
- Does a link/button end with an ornamental arrow?
- Is a gradient, shadow, texture or animation present only to add polish?
- Are numbered markers used where there is no actual sequence?
- Is yellow used as decoration instead of current/next attention?
- Does the console open with metric cards instead of actionable work?
- Does copy describe the implementation rather than the operator's task?
- Is an error vague, apologetic or missing a recovery action?
- Does an empty state fail to tell the user what to do next?
- Does any critical state rely on colour alone?

Passing this checklist is necessary but not sufficient. The screen must also express the quiet-field-instrument direction, use real ShiftMate content and make its primary job obvious at a glance.
