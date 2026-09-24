# LLM Council Transcript — Throughline ML architecture

- Timestamp: 2026-09-23T18:42:07Z
- Mode: Standard (auto-selected — default)
- Question SHA prefix: `827bd98a`
- Decision Science pass: not requested
- Workspace scan: `docs/PRODUCT_PLAN.md` and `docs/TECHNICAL_SPEC.md`; no `CLAUDE.md` or `memory/` files found.
- Prior council context: a previous quick council recommended TF-IDF/logistic regression and Ridge; the user later explicitly preferred DistilBERT and neural networks. A related journalled council on 2026-09-23 (`6fc6ce83`) recommended typed deterministic workflows with a small local classifier, while preserving stronger model challengers and richer confirmation; its outcome is not recorded. No outcome data exists for either recommendation.

## Framed question

DECISION: For Throughline, choose the implementation strategy for two ML components: (A) multilingual DistilBERT fine-tuned for English/Hindi intent classification and exported to ONNX Runtime on Android versus keyword/rule routing plus TF-IDF/logistic regression exported to JSON and executed in TypeScript; and (B) a PyTorch feed-forward neural network for task-duration correction versus Ridge regression on `log(actual/baseline)`, with split-conformal uncertainty retained in either case.

CONTEXT: Throughline is an Android-first, offline-first operator companion for Caterpillar machine operators. Voice is Vosk offline STT. The launch intent set is narrow, contextual, and safety-adjacent; consequential record creation must be read back and confirmed. Requirements include offline use from install, cold start under five seconds, UI transitions under 300 ms, offline voice command under two seconds, explainable basis/fallback indicators, and a top-three intent fallback. The plan contains about 2,500 synthetic task records derived from explicit formulas and effects over 12 simulated weeks. The estimator begins with a domain production formula and is evaluated with temporal and unseen-operator splits, MAE, MAPE, bias, and conformal coverage. Models run on-device. The simpler stack is fully specified, but implementation has not started. No target Android benchmark, real labelled bilingual utterance count, or real task-history count is known.

STAKES: Hackathon delivery risk, offline APK size and latency, bilingual intent robustness, estimator credibility, explainability to judges and operators, and avoiding claims that synthetic-data performance proves field reliability.

OPTIONS: advanced/advanced; simple/simple; or a component-wise hybrid with benchmark-gated escalation.

## Bias audit

- Sunk cost: the completed simple-stack specification may improperly determine architecture. Treat it as reusable evidence, not a commitment.
- Confirmation bias: the previous advanced preference and earlier simple recommendation invite selective evidence. Predefine identical acceptance tests.
- Anchoring: both prior positions are strong competing anchors. Start from constraints, data availability, and device measurements.
- Status quo bias: estimate remaining implementation and validation effort for every option from today.
- Planning fallacy: advanced feasibility is being discussed without hardware benchmarks or real training-set sizes. Require time-boxed prototypes and fallback deadlines.
- Narrative fallacy: sophistication may be mistaken for field robustness. Separate demo performance, measured evidence, and field claims.

## Anonymization map

- A = Executor
- B = Expansionist
- C = Red Team
- D = Outsider
- E = First Principles

## Advisor responses

### Red Team

The advanced stack can ship late or demo unreliably because DistilBERT increases APK size, integration complexity, cold-start risk, and Android inference variance without proven bilingual gains. The neural estimator can fit deterministic synthetic-generation patterns, produce impressive offline metrics, then fail to generalize to real operators and changing conditions. The root cause is committing to sophistication before establishing real-data and target-device gates. Missing hardware latency, memory, APK, bilingual-confusion, and unseen-operator benchmarks are the decision boundary. Use rules plus sparse logistic regression and Ridge as baselines; promote advanced models only on real, leakage-resistant evidence.

Confidence: high. Mind-changers: a material DistilBERT win on real bilingual safety-weighted errors within device budgets; a neural win on real unseen-operator data with valid conformal coverage.

### First Principles

Treat the components as independent evidence-allocation decisions, not one simple-versus-advanced bundle. Available information supports Ridge for duration; test DistilBERT only against a held-out bilingual, code-switched, noisy-STT challenge set. Optimize predictable failure, abstention, explanations, cold start, and confirmation rather than average metrics. The strongest option is a committed simple baseline with independently promotable challengers; the runner-up is DistilBERT for intent plus Ridge for duration if representative utterances and device benchmarks exist.

Reported confidence: 0.88, normalized to high for the council tally.

### Expansionist

The strongest outside-frame option is deterministic rules for consequential intents plus character n-gram TF-IDF/logistic regression for ambiguous English, Hindi, and Romanized Hindi. Frozen multilingual embeddings are another middle option. For duration, constrained additive corrections or monotonic splines/GAMs can capture limited nonlinearities while preserving explanations. Character n-grams plus a constrained estimator offer high upside at medium incremental effort and preserve a credible escalation path.

Reported confidence: 0.84, normalized to high for the council tally.

### Outsider

Using pharmaceutical phase-gated development as the analogy, the models are unvalidated candidates rather than “better” or “worse” technologies. Use the simple stack as a control and run blinded phase-II-style benchmarks against challengers. Pre-register safety-critical recall, abstention, calibration, bilingual slices, p95 latency, cold start, APK delta, and failure explainability. Promote DistilBERT only if it clears meaningful bilingual/ASR-noise margins without violating device budgets; do not promote the duration network until real histories show out-of-sample improvement with conformal coverage maintained.

Confidence: high.

### Executor

Throughline is in Observe/Orient. Implement simple models behind replaceable interfaces and prepare advanced challengers. Estimated effort: advanced/advanced 20–30 person-days, simple/simple 7–10, gated hybrid 11–16. Estimated priority scores were 4.5, 17.0, and 12.5 respectively. Critical missing inputs are a labelled bilingual Vosk-like corpus, device resource measurements, and real task-duration history.

Confidence: medium.

## Peer reviews

### Reviewer 1

Strongest: E, because it separates the decisions and emphasizes abstention. Weakness: it lacks numerical promotion gates and an exact simple baseline. Collective miss: deployment/evaluation mechanics, leakage-proof splitting, confirmation-cost analysis, and the offline data flywheel. `CONSENSUS STRENGTH: 5`.

### Reviewer 2

Strongest: D, because it converts uncertainty into falsifiable device and safety gates. Weakness: phase gates risk process theater without sample sizes, margins, and conflict rules. Collective miss: leakage from formula-generated rows and representative Vosk-error collection. `CONSENSUS STRENGTH: 5`.

### Reviewer 3

Strongest: D, for auditable promotion rules. Weakness: absent effect sizes, sample sizes, error costs, and timeline. Collective miss: dataset governance, code-mixed target-device audio, end-to-end confirmation latency, drift and rollback. `CONSENSUS STRENGTH: 4`.

### Reviewer 4

Strongest: E, because the components have different evidence bases. Weakness: gates cannot become statistically credible before representative data exists. Collective miss: the abstention-to-clarification-to-manual-entry fallback and privacy-safe data collection loop. `CONSENSUS STRENGTH: 4`.

### Reviewer 5

Strongest: E, because it avoids bundling the models. Weakness: no fixed latency, memory, intent-error, abstention, or confirmation-error limits. Collective miss: construct validity; synthetic data can make Ridge look excellent, and clean text does not represent code-switching or Vosk errors. `CONSENSUS STRENGTH: 4`.

Average consensus strength: **4.4/5**, triggering forced debate.

## Debate round

### Prosecutor

The consensus may optimize benchmark safety while shipping a brittle intent system that loses user trust on Hindi morphology, transliteration, code-switching, ASR corruption, and paraphrase. Users may rubber-stamp confirmations. Baseline deployment can shape telemetry and labels around its vocabulary, causing circular promotion criteria. Ridge may underfit nonlinear operator learning, fatigue, task-machine interactions, and difficult-job tails. A small regularized network can run in shadow mode now. Confirming evidence would be a blinded target-device evaluation showing DistilBERT materially reduces high-confidence wrong intents within hard resource limits.

### Defender

These weaknesses justify stronger evaluation, not immediate promotion. With little real data, DistilBERT and an FNN can produce equally confident errors outside distribution. Avoid lock-in by logging transcripts, corrections, abstentions, disagreements, latency, device context, and duration residuals behind versioned interfaces. Run the FNN in shadow mode, use selective intent acceptance and explicit fallbacks, and evaluate bilingual slices, high-confidence wrong-intent rate, calibration, tail duration error, subgroup bias, and conformal coverage. Preserve disagreement cases and audit/relabel blinded samples.

## Chairman-Consensus verdict

Council confidence: high (4/5 high, 1/5 medium, 0/5 low)

Dominant assumption: Throughline must choose a dependable production baseline before it has the bilingual speech data, real duration history, and target-device measurements needed to justify higher-capacity models.

Breakers: unacceptable Hindi/transliteration/code-switch recall from the linear system; or material nonlinear duration gains on leakage-resistant real holdouts.

### Where the council agrees

- Do not bundle the two decisions.
- The duration neural network is not justified by formula-generated synthetic records.
- Use character n-grams rather than word-only TF-IDF for the simple intent baseline.
- Pre-register leakage-resistant, end-to-end benchmarks on target Android devices.
- Implement versioned interfaces and shadow challengers.

### Where the council clashes

The genuine clash is whether advanced models should be production defaults or mandatory challengers. The Prosecutor is persuasive that sparse models can fail on bilingual and ASR-noisy tails and that confirmation can be rubber-stamped. The Defender is more persuasive that unverified complexity should not control production behavior before representative evidence exists.

### Blind spots

Template and speaker leakage, missing numerical promotion gates, absent privacy-safe logging, and an underspecified clarification/manual fallback can invalidate the comparison.

### Recommendation

Ship deterministic safety rules plus character n-gram TF-IDF/logistic regression for intent, with abstention, clarification, top-three fallback, and confirmation. Ship the domain formula with Ridge or a constrained additive residual correction. Implement DistilBERT+ONNX and the FNN as independently promotable shadow challengers and promote only after preregistered real-data and device gates are cleared.

### One thing to do first

Freeze a leakage-resistant evaluation protocol and collect the first consented bilingual Vosk utterance set on the actual target Android device.

## Chairman-Dissent verdict

Chairman-Dissent reached the same production choice but strengthened governance: make quantized DistilBERT+ONNX a mandatory same-milestone shadow challenger, benchmark high-confidence wrong intents rather than relying on aggregate F1, and preserve baseline disagreements and manual overrides so the baseline cannot bias the future training set. It also elevated character n-grams and a constrained additive/GAM estimator as the strongest middle paths.

## Dissent Ledger

- DISSENT PRESERVED: DistilBERT+ONNX must be a mandatory same-milestone shadow challenger — prevents the simpler baseline becoming permanent through organizational inertia.
- DISSENT PRESERVED: Character n-grams are the strongest practical middle path — they address morphology, Romanized Hindi, code-switching, and Vosk noise better than word-level TF-IDF.
- DISSENT PRESERVED: High-confidence wrong intents remain dangerous despite confirmation — users may rubber-stamp prompts, making demo accuracy falsely reassuring.
- DISSENT PRESERVED: Log abstentions, alternatives, and manual overrides — selective feedback otherwise creates data-path bias and corrupts promotion evidence.
- DISSENT PRESERVED: Freeze paired benchmarks and promotion thresholds before training — avoids moving goalposts after results are visible.

NOTE: Both chairmen agree on the production launch choice. The dissent materially strengthens governance by making the advanced intent challenger mandatory and the evaluation criteria precommitted.
