# Throughline — future ideas backlog (training, LLMs, other technologies)

**Status:** parked ideas, **not part of the current build**. Implement only after the planned scope (product plan §6.1 Must, then Should) is done and only if time allows. None of this is referenced by `PRODUCT_PLAN.md`, `TECHNICAL_SPEC.md` or `DATASET_SCHEMA.md`; when an idea is picked up, add it to those three documents first (requirement IDs, contracts, tests), the same way condition prep (F10-R12) and refreshers (F10-R13) were added.

**Date noted:** 24 September 2026

## Rules any idea must keep

- Offline first: the cab works fully without internet (principle 11). LLMs run **server-side only**, with F17 guardrails: facts-only input, schema-validated output, fact check, template fallback, 2 s device timeout.
- The AI never creates numbers or safety states (principle 10) and never gives machine-operating instructions (F17).
- Anything an operator sees that an LLM generated must be **human-approved first** (trainer or reviewer), or be generated at build time and reviewed before shipping.
- Learning stays private to the operator (principle 14); training only while SECURED/OFF and by operator choice (principle 8, F10-R4).
- Claims stay honest: simulated or generated data is labelled (principle 13).

## Recommended order if there is time

1. **A1 Scenario-authoring assistant** + question variants from **A2** — biggest content multiplier, zero unreviewed output to operators.
2. **A3 Voice-training utterance generation** — directly feeds the DistilBERT intent model the spec already requires (≥ 40 examples per intent per language).
3. **B1 FSRS scheduling** — small, offline upgrade to the refreshers (F10-R13).

## A. LLM ideas

| ID | Idea | Where it runs | What it does | Guardrail / blocker | Impact |
|---|---|---|---|---|---|
| A1 | **Scenario-authoring assistant for trainers** | Server + console C4 | Claude drafts new scenarios from a near-miss, a site change or a trainer's one-line prompt; generates variants (rain / night / haul-truck version), realistic wrong answers, explanations, and Hindi (later Tamil) versions | Trainer edits and approves before publishing (reuses F10-R9 pipeline); structured output + fact check. Model: Sonnet 5 in the console (no 2 s budget); Haiku 4.5 stays for cab-side calls | High — content is the bottleneck (launch pack is only 18 items) |
| A2 | **Build-time language adaptation** | Build time (content pipeline) | Simpler-wording and Hinglish versions of cards/explanations; 2–3 paraphrased variants per question so refreshers are not memorised | Human review (E-06); ships offline inside the content pack; no runtime LLM | High for low-literacy operators (Ravi) and for refresher quality |
| A3 | **Voice-training utterance generation** | Offline tooling | Claude writes Hindi, Romanised Hindi and code-switched paraphrases of each intent for `data/voice_train/intent_examples.jsonl` | Reviewed before use; `data/voice_test` stays human-written so evaluation is not flattered by generated text; disjointness checks already specified | High for voice accuracy |
| A4 | **Spoken debrief tutor** | Server, online, parked only | Short spoken back-and-forth after a scenario ("Why is the swing radius dangerous here?"), answering only from the approved card and explanation text; says "I don't know" otherwise; offline fallback = fixed explanation | **Blocker:** operator answers would pass through the server, conflicting with private learning (principle 14). Needs a product-owner decision (e.g. transient, never stored) | Medium–high, most "wow" in a demo |
| A5 | **"Ask the manual" with quoted answers** | Server, online | Retrieval over licensed Cat operation manuals and site SOPs; returns the quoted passage with page/section, not a generated answer | Needs rights to the manuals; F17 bans generated operating instructions, so extractive only; overlaps Cat AI Assistant | Medium |
| A6 | **Help-request theme summary** | Server, console | Groups "Ask a trainer" questions into themes ("8 questions about lockout on the 320") so trainers see which content confuses people | No per-operator scoring; help requests already go to the trainer | Medium |

## B. Other technologies

| ID | Technology | Use | Fit / constraint |
|---|---|---|---|
| B1 | **FSRS** (Free Spaced Repetition Scheduler) | Replace the fixed 2/7/30-day refresher intervals with per-item adaptive intervals | Small, on-device, pure TS; update F10-R13 and TC-76 |
| B2 | **Piper TTS** (offline neural text-to-speech) | More natural Hindi/English narration than device TTS | Offline; check model size against the 320 MB app budget (NFR-05) |
| B3 | **AI4Bharat IndicConformer / IndicWhisper** | Tamil speech recognition (Vosk has none, SD-01) | Could unlock Tamil voice (S2); measure latency and size on the target device |
| B4 | **IndicTrans2** | Server-side translation drafts for content packs | Alternative or cross-check to A1/A2 translation |
| B5 | **pgvector** in the existing Postgres | Retrieval index for A5 or "find a similar scenario" | No new infrastructure |
| B6 | **react-three-fiber / SVG animation** | Animated top-down replay of an incident snapshot for S9 replay and near-miss scenarios | Strong demo visual; medium effort |
| B7 | **xAPI + Learning Record Store** | Export completions to a dealer training system | Later; operator opt-in only (privacy) |
| B8 | **On-device small LLM** (Gemma/Qwen small via llama.cpp or ONNX Runtime GenAI) | Offline tutor | Already "Later" in product §6.3; 3 GB RAM and 320 MB budget make it unrealistic now |
| B9 | **LLM output evaluation** (promptfoo, or a second model grading drafts) | Automatic checks on A1 drafts before a trainer sees them | Pairs with A1 |

## Decided against

- **LangChain / LangGraph.** The spec calls the Anthropic SDK directly with structured outputs, fact checks and template fallbacks (DR-11): one call per feature, easy to test. Retrieval (A5) is simple with pgvector + the SDK. A framework would add dependencies and hide prompts that must be fact-checked. Reconsider only if a long multi-step tutor conversation (A4) is built, and even then a hand-written state machine in `packages/core` is preferred.

## Earlier e-learning ideas evaluated and skipped (for reference)

Implemented instead: **condition prep (F10-R12)** and **spaced refreshers (F10-R13)**. Skipped: queue-time audio lessons (distraction risk; already allowed while parked), morning briefing question (duplicates risk notes), confidence rating (friction for little gain), hazard-spotting pictures and branching scenarios (content-heavy variants of existing scenarios), controller practice drills (gamepad ≠ machine controls; overclaim risk), trainer site-change bulletins (communication, covered by handover/briefing), low-literacy picture mode (largely covered by narration; revisit with A2/B2), private "my learning" view (history tab exists), anonymous trainer quality view (conflicts with principle 14).
