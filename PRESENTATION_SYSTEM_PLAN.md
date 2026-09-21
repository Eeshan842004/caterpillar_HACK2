# Hackathon Presentation System Plan

## 1. Purpose

Create a reusable presentation-production system for every stage of the hackathon:

- Internal alignment.
- Problem-selection reviews.
- Mentor and sponsor checkpoints.
- Architecture and technical reviews.
- Progress updates.
- Demo rehearsals.
- Final judging presentation.
- Technical Q&A and backup material.

The system should let the team assemble a reliable deck quickly from current, verified material. It should prevent the final presentation from becoming a separate last-minute project.

## 2. Core idea: a presentation evidence pipeline

```text
Research and decisions
        ↓
Claims and evidence register
        ↓
Reusable diagrams, charts, screenshots, and metrics
        ↓
Slide briefs and speaker notes
        ↓
Intermediate decks
        ↓
Final judging deck and backup slides
```

Every important product, architecture, data, model, security, and demo activity should generate a presentation-ready artifact.

Examples:

- A user interview produces a validated pain statement and attributable note.
- An ADR produces a one-line decision and a tradeoff comparison.
- A data-quality run produces a chart and a limitations note.
- A model evaluation produces a frozen metric table and threshold chart.
- A UI milestone produces a clean screenshot at the correct aspect ratio.
- A demo rehearsal produces timing data and a backup recording.
- A threat-model review produces a simplified trust diagram and mitigation summary.

## 3. Presentation workspace structure

```text
docs/10-presentation/
├── README.md
├── presentation-context.md
├── story-arc.md
├── deck-inventory.md
├── slide-library.md
├── evidence-register.md
├── metrics-ledger.md
├── media-shot-list.md
├── source-register.md
├── terminology.md
├── style-guide.md
├── review-checklist.md
├── manifests/
│   ├── kickoff-deck.md
│   ├── checkpoint-deck.md
│   ├── architecture-review-deck.md
│   ├── demo-rehearsal-deck.md
│   └── final-deck.md
├── briefs/
│   └── slide-NN-topic.md
├── content-bank/
│   ├── problem.md
│   ├── users.md
│   ├── solution.md
│   ├── architecture.md
│   ├── data-and-ai.md
│   ├── voice.md
│   ├── security.md
│   ├── impact.md
│   ├── roadmap.md
│   └── team.md
├── visuals/
│   ├── brand/
│   ├── photos/
│   ├── icons/
│   ├── diagrams/
│   ├── charts/
│   ├── screenshots/
│   └── video/
├── decks/
│   ├── working/
│   ├── reviews/
│   ├── final/
│   └── exports/
└── archive/
```

Only create assets that have an owner and a known use. The structure is a target system, not a request for empty folders.

## 4. `presentation-context.md`

This should be the presentation team’s five-minute briefing.

Recommended structure:

```markdown
# Presentation Context

Last updated:
Owner:

## Current audience
Who will see the next deck?

## Desired outcome
What should the audience understand, decide, approve, or remember?

## Time and format
Presentation time, demo time, Q&A time, slide rules, file formats.

## Current story
Problem, user, product, proof, impact, ask.

## Strongest evidence
Three to five verified facts or results.

## Current golden demo
What will be shown live?

## Unresolved claims
Claims that lack sufficient evidence.

## Current visual assets
Links to approved diagrams, charts, screenshots, and videos.

## Next review
Date, purpose, and required outputs.
```

## 5. Deck inventory

Track every expected presentation before creating slides.

Recommended fields:

| Deck | Audience | Purpose | Desired decision | Duration | Owner | Due | Status |
|---|---|---|---|---:|---|---|---|
| Kickoff | Team | Align on planning process | Approve scope and roles | 10 min | TBD | TBD | Planned |
| Problem selection | Team/mentor | Compare candidate problems | Select one problem | 8 min | TBD | TBD | Planned |
| Architecture review | Technical reviewers | Pressure-test design | Accept/revise architecture | 12 min | TBD | TBD | Planned |
| Progress checkpoint | Mentor/sponsor | Show progress and risks | Obtain focused feedback | 7 min | TBD | TBD | Planned |
| Demo rehearsal | Team | Validate story and timing | Freeze golden path | Event-specific | TBD | TBD | Planned |
| Final judging | Judges | Demonstrate value and credibility | Rank/select solution | Rule-specific | TBD | TBD | Planned |
| Technical backup | Judges | Answer detailed questions | Establish credibility | Q&A only | TBD | TBD | Planned |

## 6. Deck manifest

Create one manifest before building each deck.

```markdown
# Deck Manifest: Name

## Audience
Roles, knowledge level, priorities, objections.

## Desired outcome
The decision or conclusion expected after the presentation.

## Constraints
Time, slide limit, template, aspect ratio, required content, submission format.

## Narrative
One paragraph describing the sequence of ideas.

## Slide plan
| # | Working title | Purpose | Evidence | Visual | Owner | Status |

## Live demo
Entry point, duration, exit point, fallback.

## Open issues
Claims, assets, decisions, or dependencies that are not ready.

## Review gates
Content review, evidence review, design review, rehearsal, final export.
```

## 7. Reusable slide brief

Write a brief before designing any important slide.

```markdown
# Slide Brief

- Slide ID:
- Deck(s):
- Owner:
- Status:

## Audience question
What question does this slide answer?

## Main point
One direct sentence.

## Evidence
Data, source, calculation, screenshot, quotation, or observed result.

## Visual form
Photo, diagram, chart, process, comparison, screenshot, or minimal text.

## Required labels
Units, dates, sample size, scenario status, caveats.

## Speaker note
What the presenter adds verbally.

## Transition
How this leads to the next slide or demo.

## Backup detail
What moves to appendix rather than the core slide.
```

## 8. Evidence register

Every factual or quantitative claim should have an entry.

Recommended fields:

| Claim ID | Claim | Evidence type | Source | Date | Calculation | Caveat | Owner | Approved for slides |
|---|---|---|---|---|---|---|---|---|

Evidence types:

- Challenge-provided fact.
- Public source.
- User or mentor feedback.
- Prototype measurement.
- Model evaluation.
- Synthetic scenario result.
- Assumption.
- Future estimate.

Presentation rules:

- Never present an assumption as a measured outcome.
- Label synthetic results clearly.
- Preserve units, time periods, denominators, and sample sizes.
- Store calculations or scripts behind headline metrics.
- Record limitations that affect interpretation.
- Use the same number and wording across all decks unless evidence changes.

## 9. Metrics ledger

The metrics ledger prevents inconsistent numbers between slides, README files, demos, and judge answers.

Recommended fields:

- Metric ID.
- Display name.
- Definition.
- Formula.
- Unit.
- Time window.
- Dataset/version.
- Baseline.
- Current/prototype value.
- Target or scenario estimate.
- Confidence/uncertainty.
- Owner.
- Last verified date.
- Where used.

Example metric categories:

- User time saved.
- Alert precision and recall.
- Lead time before an event.
- False alerts per asset-day.
- Avoided idle time.
- Estimated fuel or emissions reduction.
- Voice time to first audio.
- Task completion time.
- Data import success and rejected rows.
- Demo startup/reset time.

## 10. Source register

Track external facts and media separately from evidence summaries.

For each source record:

- Source ID.
- Title.
- Publisher/author.
- Direct URL or repository path.
- Publication and access date.
- Supported claims.
- Usage rights or attribution requirements.
- Screenshot/figure restrictions.
- Slide and speaker-note references.

This makes final citations and licensing checks much easier.

## 11. Content bank

Maintain polished, reusable content blocks. Each block should have short, medium, and detailed versions.

### Problem

- One-sentence problem.
- 30-second explanation.
- Full workflow and consequences.

### User

- Primary persona.
- Environment and constraints.
- Current workflow.
- Reason the problem matters now.

### Solution

- One-line description.
- Three-step workflow.
- Detailed capability explanation.

### Differentiation

- Why existing workflow is insufficient.
- What changes for the user.
- Which technical capability makes that possible.

### Architecture

- One-sentence architecture.
- Simplified diagram description.
- Technical component explanation.

### Data and AI

- Data sources.
- Baseline and advanced method.
- Evaluation and limitations.
- Explainability and oversight.

### ElevenLabs voice

- User reason for voice.
- Supported voice workflow.
- Credential/privacy model.
- Text fallback.
- Measured latency or clearly labelled expectation.

### Security and trust

- Sensitive data handled.
- Core protections.
- Human confirmation points.
- Known prototype limitations.

### Impact

- Measured prototype result.
- Scenario estimate.
- Operational outcome.
- Adoption path.

### Roadmap

- What works now.
- What needs validation.
- What a production pilot requires.

## 12. Visual asset library

### 12.1 Brand kit

Prepare:

- Approved product name and one-line description.
- Logo or wordmark, only if one is genuinely needed.
- Color palette with accessible contrast.
- Typography.
- Light and dark background variants.
- Partner/sponsor logo rules.
- Slide aspect ratio.
- Footer and citation style.
- Chart colors and status colors.

Avoid spending excessive hackathon time on a logo. The product and evidence matter more.

### 12.2 Diagram library

Maintain editable Excalidraw sources and presentation-ready exports for:

- System context.
- Simplified judge architecture.
- Detailed engineering architecture.
- Golden user journey.
- Data flow.
- Analytics pipeline.
- ElevenLabs voice sequence.
- Trust boundaries.
- Deployment.
- Failure/fallback behavior.

Create simplified and detailed variants from the same accepted architecture.

### 12.3 Chart library

Prepare reusable chart specifications for:

- Trend over time.
- Before/after comparison.
- Ranked risk.
- Distribution.
- Actual versus baseline.
- Confusion matrix.
- Precision/recall or threshold tradeoff.
- Operational impact waterfall.
- Scenario comparison.

Every chart needs:

- Question it answers.
- Source data.
- Units and date range.
- Direct labels where practical.
- Annotation of the important event.
- Accessible colors.
- Clear distinction between measured, synthetic, and estimated data.

### 12.4 Screenshot library

For each important workflow capture:

- Clean base screenshot.
- Annotated version if explanation is needed.
- Light/dark variant only if both are used.
- Desktop presentation crop.
- Optional mobile/tablet crop.
- Capture date and application revision.
- Dataset/scenario identifier.
- Privacy check.

Do not use screenshots containing debug controls, browser clutter, personal information, secrets, broken states, or unexplained placeholder data.

### 12.5 Video and audio library

Prepare:

- Short silent product loop for background use, if helpful.
- Backup clip of the golden demo.
- Backup clip of ElevenLabs voice interaction.
- Clean audio sample for noisy venues.
- Caption file or transcript.
- Still image for video failure.

Keep media embedded or locally available. Do not depend on streaming during judging.

## 13. Architecture diagram production

### Canonical Excalidraw workflow

1. Architecture owners approve the underlying design.
2. Create the detailed engineering diagram.
3. Review boundaries, labels, protocols, and optional components.
4. Derive a simplified judge-facing diagram.
5. Export transparent SVG and high-resolution PNG.
6. Add version/date and source reference.
7. Insert the simplified export into the core deck.
8. Put the detailed version in backup slides.
9. Re-export after any accepted architecture change.

### Judge-facing architecture diagram

It should make these relationships clear within roughly 20 seconds:

- Who uses the product.
- What enters the system.
- Where core product logic lives.
- Where analytics/AI contributes.
- How ElevenLabs voice connects.
- What data store is used.
- Which systems are external or optional.
- How a result becomes a user action.

### Technical architecture diagram

It may additionally include:

- Runtime/container boundaries.
- Protocols.
- Authentication and token exchange.
- Trust boundaries.
- Queues/background jobs.
- Observability.
- Mocks/fallbacks.
- Deployment units.

## 14. Presentation-ready outputs from each workstream

### Product and research

- Validated problem statement.
- Persona and current workflow.
- Pain/evidence summary.
- Alternative approaches considered.
- Success-metric definition.

### UX and frontend

- User journey.
- Wireflow.
- Clean screenshots.
- Before/after workflow comparison.
- Accessibility summary.

### Architecture and platform

- Context and component diagrams.
- Integration catalog.
- Deployment and fallback view.
- Architecture tradeoffs.
- Reliability measurements.

### Data and AI

- Data lineage diagram.
- Data-quality snapshot.
- Baseline comparison.
- Evaluation charts.
- Model/rule explanation.
- Limitations and responsible-use summary.

### Voice

- Reason voice helps the user.
- Voice interaction sequence.
- Transcript screenshot.
- Latency and failure measurements.
- Credential/privacy explanation.
- Text fallback demonstration.

### Security and privacy

- Trust-boundary diagram.
- Top threats and mitigations.
- Confirmation and audit behavior.
- Retention and consent summary.

### Demo and QA

- Verified golden path.
- Test/status summary.
- Rehearsal timings.
- Backup screenshots and video.
- Known limitations.

### Team

- Contribution summary.
- Key decisions or learning.
- Contact/submission details.

## 15. Intermediate deck recipes

### 15.1 Kickoff and alignment deck

Purpose: approve how the team will work before the problem statement arrives.

Suggested slides:

1. Hackathon objective and constraints.
2. Likely challenge families.
3. Starter-pack scope and non-goals.
4. Planning artifact system.
5. Proposed architecture boundaries.
6. Voice opportunity and safeguards.
7. Team roles and decision process.
8. Readiness gate and next actions.

### 15.2 Problem-selection deck

Purpose: choose among candidate problems after reveal.

Suggested slides:

1. Official challenge and judging criteria.
2. Candidate users and pains.
3. Opportunity comparison matrix.
4. Data and feasibility comparison.
5. Expected value and differentiation.
6. Risk and dependency comparison.
7. Recommended problem and MVP.
8. Decision required.

### 15.3 Concept review deck

Purpose: validate the product idea before substantial building.

Suggested slides:

1. User and current workflow.
2. Problem evidence.
3. Proposed workflow.
4. Golden use case.
5. Wireflow or storyboard.
6. Success metrics.
7. Assumptions and validation plan.
8. Scope and non-goals.

### 15.4 Architecture review deck

Purpose: accept or revise technical design.

Suggested slides:

1. Requirements and quality priorities.
2. System context.
3. Component/runtime architecture.
4. Data flow and contracts.
5. ElevenLabs voice sequence.
6. Security and trust boundaries.
7. Failure and fallback behavior.
8. Options, ADR decisions, and unresolved questions.

### 15.5 Progress or mentor checkpoint deck

Purpose: obtain useful feedback rather than merely report activity.

Suggested slides:

1. Problem and chosen outcome.
2. Current end-to-end workflow.
3. What is implemented and verified.
4. Evidence or current metrics.
5. Short demo or screenshots.
6. Main risks and unknowns.
7. Specific questions for the mentor.
8. Work remaining and next checkpoint.

### 15.6 Data/model review deck

Purpose: assess whether analytical claims are credible.

Suggested slides:

1. Decision supported by the model/rule.
2. Dataset, lineage, and quality.
3. Baseline method.
4. Candidate model and features.
5. Evaluation design.
6. Results and threshold tradeoffs.
7. Error analysis and limitations.
8. Operational integration and human oversight.

### 15.7 Demo-freeze deck

Purpose: decide what will appear in the final presentation and freeze it.

Suggested slides:

1. Final story arc.
2. Golden demo steps and timing.
3. Verified claims and metrics.
4. Final architecture.
5. Remaining defects and decisions.
6. Dependency fallback matrix.
7. Final slide/media ownership.
8. Go/no-go decision.

### 15.8 Rehearsal review deck

Purpose: refine delivery after a timed run.

Suggested content:

- Actual versus target timing.
- Confusing moments.
- Demo latency or failure observations.
- Questions the rehearsal audience asked.
- Slides to cut or simplify.
- Speaker transitions.
- Backup-path readiness.

This can be a working document rather than a polished presentation.

## 16. Final judging deck

The exact slide count should follow event rules. A practical default is 8–12 core slides plus backup slides.

### Core narrative

1. **Title and product statement**
   - Product name.
   - One direct sentence explaining the value.

2. **Primary user and problem**
   - Who experiences the problem.
   - Current workflow and specific pain.

3. **Operational consequence**
   - Evidence of time, cost, risk, downtime, safety, or sustainability impact.

4. **Solution workflow**
   - How the user moves from signal to decision or action.

5. **Live demonstration**
   - Minimal setup text.
   - State what judges should observe.

6. **Technical architecture**
   - Simplified Excalidraw export.
   - Show data, intelligence, voice, and action path.

7. **Data and decision logic**
   - Baseline/model, evidence, explainability, and human oversight.

8. **Voice interaction**
   - Why voice improves this specific workflow.
   - Security and fallback in one concise explanation.

9. **Validation and impact**
   - Measured prototype results.
   - Clearly labelled scenario estimates where necessary.

10. **Trust and limitations**
    - Main safeguards.
    - What the prototype does not claim.

11. **Adoption path**
    - Integration, pilot, and scale considerations.

12. **Closing**
    - Restate the user outcome.
    - Clear final ask or takeaway.

### Backup slide groups

- Architecture detail.
- API and data contracts.
- Evaluation methods and results.
- Data quality and lineage.
- Security/privacy/threat model.
- ElevenLabs integration details.
- Cost and quota assumptions.
- Alternative solutions and tradeoffs.
- Implementation status.
- Team contributions.
- Sources and acknowledgements.

## 17. Speaker notes system

Each slide should have notes containing:

- Intended duration.
- Opening sentence.
- Main explanation.
- Number or term that must be stated precisely.
- What not to claim.
- Transition to the next slide/demo.
- Likely judge question.
- Source citations not visible on the slide.

Keep slide text concise. Put nuance, caveats, and citations in notes unless the audience must see them.

## 18. Versioning and naming

Recommended filename format:

```text
YYYYMMDD-HHMM_deck-purpose_vNN_status_owner.pptx
```

Examples:

```text
20260921-1800_architecture-review_v03_review_RS.pptx
20260923-0900_final-pitch_v07_candidate_team.pptx
20260923-1400_final-pitch_v08_frozen_team.pptx
```

Statuses:

- `working`
- `review`
- `candidate`
- `frozen`
- `submitted`

Rules:

- Never overwrite the submitted version.
- Archive superseded decks.
- Record which application revision and dataset each candidate deck represents.
- Use one designated owner to produce the final export.

## 19. Asset capture triggers

Capture assets throughout the project at defined moments.

| Trigger | Required presentation output |
|---|---|
| Problem selected | Final problem statement and opportunity slide brief |
| Persona validated | User quote/note and current-workflow visual |
| ADR accepted | Decision summary and updated diagram |
| Data imported | Data-quality snapshot and lineage update |
| Baseline evaluated | Frozen results table and chart |
| UI workflow stabilized | Clean screenshots and short recording |
| Voice integration works | Transcript screenshot, audio/video backup, latency observation |
| Threat model reviewed | Trust-boundary diagram and safeguards summary |
| Golden path passes | Demo recording and verified step list |
| Demo freeze declared | Final screenshots, architecture exports, and deck candidate |

## 20. Review gates

### Gate 1: Story review

- Clear user and problem.
- One coherent narrative.
- No duplicate slides.
- Demo supports the narrative.

### Gate 2: Evidence review

- Every claim has evidence or an explicit assumption label.
- Metrics match the ledger.
- Synthetic and estimated results are labelled.
- Sources and permissions are recorded.

### Gate 3: Technical review

- Architecture matches implementation.
- Diagrams reflect accepted ADRs.
- Security and AI limitations are accurate.
- No feature is described as complete unless verified.

### Gate 4: Visual review

- Slide titles identify the real subject.
- Text is readable at distance.
- Visuals have a purpose.
- Charts include units and labels.
- Screenshots are clean and current.
- Layout and terminology are consistent.

### Gate 5: Rehearsal review

- Presentation fits the allotted time.
- Demo entry and exit are smooth.
- Speakers know transitions.
- Backup paths are ready.
- Likely questions have owners and answers.

### Gate 6: Export review

- PPTX and PDF both render correctly.
- Fonts, videos, audio, and diagrams work on the presentation device.
- Offline copy works.
- Final filename and version are correct.
- Submission package contains only intended material.

## 21. Presentation quality rules

- Use one main idea per slide.
- Prefer direct language over slogans and jargon.
- Keep the title slide minimal.
- Prefer one coherent composition over a grid of dashboard-like cards.
- Use the fewest words that preserve accuracy.
- Do not repeat what the speaker can say unless the audience needs to retain it.
- Make tables and charts editable when practical.
- Preserve source calculations for all metrics.
- Use original logo and brand assets.
- Never stretch images or diagrams.
- Avoid tiny text; cut content or move detail to backup slides.
- Add citations in speaker notes and visibly where rules require them.
- Never use an attractive visual that changes the meaning of the evidence.

## 22. Presentation readiness checklist

### Reusable system

- [ ] Deck inventory exists.
- [ ] Presentation context has an owner.
- [ ] Evidence and source registers exist.
- [ ] Metrics ledger exists.
- [ ] Content bank uses approved terminology.
- [ ] Brand and chart rules are defined.
- [ ] Excalidraw source/export process is defined.
- [ ] Screenshot and media capture process is defined.
- [ ] Slide and deck manifest templates exist.

### Intermediate presentations

- [ ] Audience and desired decision are explicit.
- [ ] Deck uses current context and accepted ADRs.
- [ ] Open questions are framed for useful feedback.
- [ ] Status distinguishes planned, implemented, mocked, and verified work.
- [ ] Feedback and decisions are captured after the presentation.

### Final presentation

- [ ] Event rules and timing are confirmed.
- [ ] Final story and golden demo agree.
- [ ] All core claims pass evidence review.
- [ ] Architecture matches the frozen build.
- [ ] Final screenshots use the frozen scenario.
- [ ] Backup slides answer expected technical questions.
- [ ] Speaker notes and transitions are complete.
- [ ] Live demo and fallback media are rehearsed.
- [ ] PPTX, PDF, and offline media are verified on the presentation device.
- [ ] Submitted files are preserved unchanged.

## 23. Recommended preparation order

1. Create the deck inventory and identify event-specific presentation rules.
2. Define the evidence register, metrics ledger, and source register.
3. Create the reusable content bank and terminology list.
4. Agree on visual style, aspect ratio, chart rules, and Excalidraw conventions.
5. Write manifests for the kickoff, architecture review, checkpoint, and final decks.
6. Assign presentation-ready outputs to every workstream.
7. Define asset capture triggers and owners.
8. Create intermediate decks only when their decision purpose is clear.
9. Update the final-deck manifest continuously as evidence improves.
10. Freeze the final story only after the golden demo and claims are verified.
