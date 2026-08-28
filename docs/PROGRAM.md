# Atlas Program

How this system becomes genuinely good over years, rather than an impressive demo that
stops being read after three weeks.

`docs/BUILD_QUEUE.md` answers *what to build next*. This document answers *what makes it
worth building at all*: where quality actually comes from, what Atlas can and cannot
honestly promise, how it accumulates knowledge, and what hardware, skills and habits the
owner needs at each stage.

---

## 1. Where quality actually comes from

The instinct is that a decision system gets better by using a smarter model. That is the
least binding constraint. Four factors determine whether Atlas is useful, in descending
order of leverage:

| Factor | Why it dominates | How to improve it |
| --- | --- | --- |
| **Completeness of personal state** | An impact engine can only reason about exposure it knows about. Unrecorded cash, an untracked deadline or a missing income stream makes every downstream conclusion wrong in a way no model can detect. | Queue 07, then disciplined upkeep |
| **Feedback density** | Calibration requires resolved decisions. Ten decisions a year cannot calibrate anything; two a week can. | Journal every material judgement, resolve outcomes on schedule |
| **Signal-to-noise of the daily output** | A brief that is 80% noise trains the owner to stop reading, after which the system's real accuracy is irrelevant. | Materiality thresholds, the Attention Covenant, ruthless source pruning |
| **Model capability** | Matters for causal synthesis and challenge, and frontier models are already sufficient for it. | Provider routing; revisit yearly |

The practical consequence: **spend effort on state completeness and the feedback loop
before spending it on models, agents or sources.** A system with excellent personal state
and a mediocre model beats the reverse, every time.

### The anti-pattern

The failure mode this program is designed against is *impressive breadth with no
compounding*: forty sources, nine agents, a beautiful dashboard, and no record of whether
any of it was ever right. That system feels advanced and learns nothing.

---

## 2. What Atlas can and cannot honestly do

This section exists so that expectations do not quietly inflate into disappointment, and
so no one ever acts on a promise Atlas cannot keep.

### Trading and markets

**Atlas will not generate trading alpha, and should never be built as if it might.**
Public data, public news and a general-purpose model do not produce a statistical edge
against participants with proprietary data, co-located execution and dedicated research
teams. Any system that appears to find alpha this way has almost certainly found
overfitting.

What Atlas genuinely does, and where the money actually is for an individual:

- **Exposure awareness.** What you actually hold, in what currencies, in what
  jurisdictions, and what a −30% move in each does to you. Most people cannot answer this
  and are wrong when they guess.
- **Risk and concentration discipline.** Deterministic policy checks that flag a breach
  *before* it becomes a loss — position size, single-asset concentration, stablecoin
  exposure, liquidity runway.
- **Regime awareness.** Not prediction: recognition. Knowing whether liquidity is
  expanding or contracting changes how much risk is appropriate, independent of any view
  on a specific asset.
- **Behavioural error removal.** Panic selling, FOMO buying, holding a position past your
  own stated thesis. A journal that records what you believed at decision time is the
  only effective defence, because it removes hindsight.
- **Cash and runway management.** Boring, deterministic, and the single highest-value
  output for anyone with variable income.

The honest framing: Atlas improves **decision quality and risk discipline**, not return
prediction. That is a far more reliable source of financial outcome for an individual
than signals.

### Relocation and geography

Atlas will not say "move to Milan". It will say: here is your current exposure to Turkey
across currency, income, deadlines and social stress; here is what changed this month;
here is how your candidate geographies score **on the criteria you defined**; here is
which deadline is closest and what it requires. The judgement stays with the owner; the
system removes the part humans are bad at — holding twelve interacting variables in
working memory and noticing slow drift.

### Life decisions generally

Atlas is strongest where a decision depends on **many slowly-changing facts that are
tedious to track** and weakest where it depends on values, relationships or private
information the system does not hold. It should be explicit about which case it is in.
An `INFERRED_CAUSAL` or `SPECULATIVE` impact is a prompt to think, never an instruction.

---

## 3. How Atlas actually learns

"Infinite self-education" is real, but it is not the model retraining itself. It is five
concrete mechanisms, all of which write into **structured storage**, not model weights.
This matters enormously: because learning accumulates in Postgres rather than in a
fine-tune, **changing or upgrading the model does not erase what the system has learned.**
That property is the direct consequence of ADR-0002, and it is the reason the architecture
is worth its overhead.

### 3.1 Scenario calibration

Every scenario carries a probability. When its horizon resolves, the outcome is stored and
scored with a proper scoring rule (Brier). Over months this produces a map of *which
scenario families Atlas is bad at* — for example, consistently overconfident on
geopolitical timing, well-calibrated on liquidity. That map then adjusts priors and
confidence bounds. This is Queue 10 and Queue 12 working together.

### 3.2 Decision retrospectives

Each decision stores the evidence, scenario probabilities and personal state available at
decision time. Retrospective evaluation asks whether the *premise* was right, separately
from whether the *outcome* was good — the distinction that separates skill from luck. A
correct decision with a bad outcome must not be scored as a mistake, or the system learns
to be timid.

### 3.3 Rule promotion — the core compounding mechanism

This is where Atlas becomes cumulatively smarter rather than merely experienced.

```
INFERRED_CAUSAL impact  →  observed to hold N times with adequate evidence
                        →  proposed as a DIRECT_RULE
                        →  owner reviews and accepts
                        →  becomes deterministic code
```

Every promotion moves a judgement from the expensive, variable, model-dependent path to
the cheap, deterministic, testable path. After a year, a meaningful share of Atlas's
reasoning is deterministic rules **derived from the owner's own history** — which is
precisely what no general model can offer, and what makes the system progressively
cheaper and faster rather than more expensive.

Guardrail: promotion is always owner-approved and always reversible. A promoted rule is
code, so it is versioned, tested, and can be demoted.

### 3.4 Source reliability learning

`default_reliability` is a prior, not a verdict. Track per source: how often its claims
were corroborated, how often it led, how often it was noise. A class-D channel that
consistently front-runs confirmed events earns weight; a class-B publication that mostly
recycles earns less. This is deterministic bookkeeping over the provenance chain that
already exists.

### 3.5 Prompt and extraction improvement

Prompts are versioned assets. Extraction failures, schema-validation rejections and
disagreement between models are recorded per prompt version. Improvement here is
measured against golden fixtures, not vibes.

### What is deliberately **not** on this list

Fine-tuning a model on personal data. It is expensive, it leaks personal data into
weights, it must be redone at every model upgrade, and — critically — it makes learning
**opaque and non-auditable**, which contradicts A05. Revisit only if a specific, measured
task fails under prompting and retrieval. It is the last resort, not the goal.

---

## 4. Data as the compounding asset, and how privacy is preserved

The value of Atlas at month one is a daily brief. The value at month eighteen is
qualitatively different: *"the last three times liquidity contracted while you were this
concentrated, here is what you did and how it turned out."* No chat assistant can produce
that, because it requires a continuous, structured, provenance-linked record of a
specific life. That record is the asset. Everything else is machinery.

Which is exactly why privacy is not a feature bolted on later — it determines what may
be collected at all.

### Data classification and routing

Every piece of data carries a sensitivity tier, and the tier determines which model may
ever see it:

| Tier | Content | May be sent to |
| --- | --- | --- |
| **L0 — Public** | News, market prices, macro series, regulations | Any provider |
| **L1 — Derived public** | World state, narratives, events, scenarios | Any provider |
| **L2 — Personal structured** | Balances, positions, currencies, runway, geography | Frontier provider **only** pseudonymised: quantities as ratios or buckets, no identifiers, no institution names |
| **L3 — Sensitive personal** | Residency documents, deadlines tied to identity, health, relationships, precise location, account identifiers | **Raw L3: local model only. Never crosses the external-model perimeter.** |

This is why the local-model path in §7 is not ideological. It is what makes raw L3 usable
for model reasoning. L3 may be stored in managed PostgreSQL under the storage controls in
`SECURITY.md`, but until a local model handles it Atlas does not send it to a model. A
separate deterministic L2 privacy projection may be routed externally with provenance.

### Non-negotiables

Everything in `docs/SECURITY.md` applies, and two rules dominate:

1. **Seed phrases, private keys, withdrawal-capable credentials and banking passwords are
   never stored.** No feature justifies an exception.
2. **The repository is public; the data is not.** Personal state terminates in the
   database and its encrypted backups. It never enters a commit.

### Backups are part of privacy

An encrypted, tested, off-site backup is a privacy control, not just an availability one:
losing the accumulated record destroys the asset, and an unencrypted backup destroys the
confidentiality. `pg_dump` → age/gpg encryption → object storage, with a **restore test
every quarter**. An untested backup is not a backup.

---

## 5. Accuracy: how it is measured rather than asserted

"Accurate" is meaningless unless it is measurable. Four distinct things get measured, and
they fail differently:

| What | Metric | Failure it catches |
| --- | --- | --- |
| **Factual extraction** | Precision/recall against golden fixtures | The model inventing or dropping facts |
| **Deduplication and event merging** | Cluster purity on 20–50 known historical clusters | The same story counted five times as five events |
| **Probabilistic judgement** | Brier score, calibration curves, by scenario family | Confident wrongness — the most dangerous failure |
| **Usefulness** | Owner marks each brief item useful / noise / wrong | A system that is accurate and irrelevant |

The fourth is the one most systems skip and the one that decides whether Atlas survives.
It costs the owner about a minute a day and is the highest-value minute in the process.

### Calibration is the real target

A system that says "70%" and is right 70% of the time is vastly more useful than one that
says "90%" and is right 75% of the time, even though the second is "more accurate" by
naive scoring. Calibration is what makes a probability actionable. This is A12 expressed
as a measurement programme, and it is why `probability_method` is stored alongside every
probability.

### Regression gates

Golden fixtures and calibration sets are **CI artefacts**. A prompt change that improves
prose but degrades extraction recall must fail the build. Without this, quality drifts
downward invisibly with every "small improvement".

---

## 6. Phases, gated by evidence rather than dates

Each phase has an **exit trigger**. Do not start the next phase because time passed;
start it because the trigger fired. Skipping a trigger is how systems become expensive
and unloved.

### Phase 0 — Prove the loop (now)

Queue 01–14. One vertical slice: ~7 sources, 10 world dimensions, real personal state, a
daily brief.

- **Infrastructure:** laptop + Neon PostgreSQL 16, AWS Frankfurt (`eu-central-1`). Local
  development and tests stay on Docker PostgreSQL 16.
- **Cost:** ~$0–30/month including model calls.
- **Exit trigger:** the daily cycle runs 30 consecutive days without manual repair, and
  the owner has read 30 briefs and marked them.

### Phase 1 — Make it continuous

Alerts, scheduling, Telegram surface (Queue 15), dashboard (Queue 16).

- **Infrastructure:** small VPS — 4 vCPU / 16 GB RAM / ~200 GB NVMe (Hetzner-class,
  €15–25/month). Docker Compose: Postgres, API, worker, Caddy for TLS.
- **Exit trigger:** ≥50% of briefs contain at least one item the owner marked useful, and
  no `ACTION` alert has been a false alarm for a month.

### Phase 2 — Make it calibrated

Queue 12 outcomes running in earnest, rule promotion (§3.3) active, MCP surface (Queue 17)
so the owner can interrogate state conversationally.

- **Infrastructure:** unchanged, plus disciplined backups with quarterly restore tests.
- **Exit trigger:** ≥50 resolved decisions, a calibration report exists, and Brier scores
  beat the base rate on at least one scenario family.

### Phase 3 — Bring it home

Personal server; local models for extraction and all L3 data; semantic memory (Queue 18).

- **Entry triggers — any one is sufficient:**
  (a) L3 data becomes material to decisions;
  (b) model spend exceeds ~€150/month, at which point local inference amortises;
  (c) an external dependency becomes a real availability or privacy risk.
- **Exit trigger:** the FAST_MODEL class runs entirely locally with no measured quality
  loss on golden fixtures.

### Phase 4 — Depth

Quant Lab (Queue 19, Qlib), regime research, richer causal modelling, possibly local
reasoning models.

- **Entry trigger:** Phase 2 exit passed **and** the system has ≥12 months of continuous
  history. Backtesting on less is self-deception.

---

## 7. Hardware ladder

The single most common expensive mistake is buying a GPU first. **Most of Atlas's value
is deterministic code that runs comfortably on any modern CPU.** Buy compute when a
measured constraint demands it.

| Stage | Machine | Approx. cost | Runs |
| --- | --- | --- | --- |
| 0 | Existing laptop + managed Postgres | ~€0 | Everything, single-user, non-continuous |
| 1 | VPS: 4 vCPU / 16 GB / 200 GB NVMe | €15–25/mo | Postgres, API, worker, scheduler, alerts, dashboard, 24/7 |
| 2 | Mini-PC or tower, **no GPU**: 8–16 cores, 64 GB RAM, 2 TB NVMe | €700–1,200 | All of the above locally + embeddings + small extraction models on CPU |
| 3a | Apple Silicon desktop, 96–192 GB unified memory | €4,000–9,000 | 30B–70B-class inference, quiet, excellent performance per watt |
| 3b | Workstation + 1–2 GPUs, 48–96 GB VRAM total | €5,000–15,000 | Same class with higher throughput, louder, higher power draw |

Notes that matter more than the specific numbers:

- **RAM and fast NVMe before GPU.** Postgres with pgvector, full-text search and a growing
  event store benefits far more from memory and disk than from a graphics card.
- **Unified-memory Apple machines are unusually well suited** to single-user local
  inference: memory capacity is the binding constraint for large models, and 128 GB of
  unified memory holds models that would need several discrete GPUs. Throughput is lower,
  but a personal system runs one request at a time.
- **VRAM sizing, roughly:** a 30B-class model at 4–5-bit quantisation needs ~20–24 GB;
  a 70B-class model needs ~40–48 GB; leave 20–30% headroom for context.
- **Verify current parts before buying.** This ladder describes capability tiers; specific
  models and prices move quickly, and the right purchase is the cheapest machine that
  clears the tier you actually need.
- **Power, noise and heat are real constraints** in a home, and they are the reason many
  home GPU builds end up switched off. Factor them before purchase, not after.

---

## 8. Local model strategy

Migrate by **task class**, never all at once. The architecture already supports this:
`packages/atlas/providers` defines the port, so switching a class is configuration, not a
rewrite.

| Class | Workload | Local viability | Migration order |
| --- | --- | --- | --- |
| **Embeddings** | Semantic search, near-duplicate detection | Excellent — small models, run on CPU | **First**, immediately |
| **FAST_MODEL** | Extraction, classification, normalisation, entity resolution | Strong — this is ~80% of call volume and the least demanding reasoning | **Second**, Phase 3 entry |
| **WRITE_MODEL** | Brief prose from approved structures | Adequate at 30B+ — the structure is already decided, only phrasing is generated | **Third** |
| **REASON_MODEL** | Causal synthesis, scenario challenge, falsification | Frontier models remain clearly better; this is where Atlas's judgement lives | **Last, and only if measured to be adequate** |

The endpoint is a **hybrid**, not full locality: L3 data and high-volume mechanical work
run locally; hard causal reasoning over L0/L1/pseudonymised-L2 uses whatever model is
best. Treat "everything local" as a preference to be justified by measurement, not a
destination.

**Serving:** `vLLM` for throughput and production behaviour on GPU; `llama.cpp` / Ollama
for simplicity and Apple Silicon; LM Studio for experimentation. Quantisation: GGUF Q5/Q6
or AWQ/GPTQ 4-bit — measure quality on golden fixtures before and after, because
quantisation damage is task-specific and shows up first in structured-output compliance.

**The migration gate:** a class moves local only when it passes the same golden fixtures
at the same threshold as the frontier model it replaces. "It seemed fine in chat" is not
evidence.

---

## 9. Tooling

| Area | Choice | Why |
| --- | --- | --- |
| Environment | `uv` | Fast, lockfile-based, reproducible; already in use |
| Lint / format | `ruff` | One tool, fast enough to run on every save |
| Types | `mypy --strict` | The domain is the contract; untyped domain code defeats the point |
| Tests | `pytest` | Plus the boundary and determinism guards already in place |
| Migrations | Alembic | Queue 01 |
| Containers | Docker Compose | Sufficient through Phase 3; Kubernetes is an anti-goal |
| LLM tracing and cost | Langfuse or Phoenix, OpenTelemetry-compatible | Per-run cost and latency are required by §28 of the blueprint; without them spend becomes invisible |
| Evals | Own harness on pytest + golden fixtures | Generic eval tools do not express point-in-time and provenance constraints |
| Secrets | Provider secret manager; 1Password or Doppler for local | Never in the repo, never in `.env` beyond local dev |
| Backups | `pg_dump` → age/gpg → object storage | With a quarterly restore test |
| Implementation agents | Claude Code / Codex, one queue item at a time | The queue and ADR discipline exist to keep agents inside the architecture |
| Architecture review | A second model, given the docs | Adversarial review of decisions is worth more than more generation |

---

## 10. Skills

Be realistic: no one becomes expert in all of this in a year. Split the surface.

### Owner-only — cannot be delegated

- **Defining criteria.** What "a good country" means for you; what risk is acceptable;
  what a policy threshold should be. Atlas can evaluate criteria; it cannot author your
  values.
- **Judging output quality.** Distinguishing a useful brief from a well-written one. This
  is the feedback signal the whole system learns from.
- **Journal discipline.** Recording decisions *before* outcomes are known. Tedious, and
  the entire calibration loop depends on it.
- **Reading a probability correctly.** Understanding what 0.7 confidence means and what it
  does not.

### Worth learning, realistically over 6–12 months

- **SQL and thinking in data.** Non-negotiable — the canonical state is relational, and
  being unable to query it makes you dependent on the interface for everything.
- **Applied probability:** base rates, Bayesian updating, proper scoring rules,
  calibration. This is the intellectual core of Atlas, and roughly a month of study.
- **Portfolio and risk mathematics:** exposure, concentration, correlation, drawdown,
  position sizing, runway. Risk management, explicitly *not* trading technique.
- **Structured-output discipline:** schemas, validation, why free-text model output is
  unusable as state.
- **Security basics:** threat modelling, least privilege, secret handling.

### Delegated to agents

Queue implementation, tests, migrations, adapters, refactors, documentation upkeep. The
architecture documents exist precisely so this delegation stays safe.

### Hired, only when triggered

- **Lawyer/tax adviser** — before any commercial step, and before acting on any residency
  or cross-border tax conclusion. Atlas produces analysis, never legal advice.
- **DevOps/SRE** — one engagement when moving to a personal server, to get backups,
  monitoring and access control right.
- **Data engineer** — only if ingestion becomes the measured bottleneck.

---

## 11. Knowledge

Narrow and load-bearing, rather than a long reading list:

1. **Calibration and forecasting** — Tetlock, *Superforecasting*. This is Atlas's core
   discipline; read it first.
2. **Decision quality vs outcome quality** — Duke, *Thinking in Bets*. The distinction
   that makes retrospectives meaningful rather than punitive.
3. **Proper scoring rules** — Brier score, log score, calibration curves. A few papers or
   a good blog series; needed to implement Queue 10 and 12 correctly.
4. **Causal reasoning** — Pearl, *The Book of Why* for intuition. Essential for knowing
   what the Impact Engine may and may not claim; the difference between correlation and a
   causal chain is the difference between `INFERRED_CAUSAL` and a false promise.
5. **Risk and tail thinking** — Taleb on fragility, for scenario design. Read critically.
6. **Risk management, not trading** — any solid text on portfolio risk. Explicitly avoid
   the technical-analysis genre; it will pull the system toward signals and away from
   exposure.
7. **Threat modelling** — OWASP materials; enough to reason about a system holding your
   entire financial picture.

---

## 12. Operating rhythm

The system's improvement rate is set by this rhythm, not by development speed.

| Cadence | Activity | Time |
| --- | --- | --- |
| **Daily** | Read the brief. Mark each item useful / noise / wrong. | 10–15 min |
| **Daily, when relevant** | Journal any material decision **before** the outcome is known. | 2 min |
| **Weekly** | Resolve due outcomes. Review open watches and deadlines. Prune noisy sources. | 30 min |
| **Monthly** | Calibration report: where was Atlas wrong, and was it wrong confidently? Review promoted rules. | 1 hour |
| **Quarterly** | Architecture review. Backup restore test. Re-read ADRs against reality; write new ones where the system has drifted. | Half a day |

The daily marking step looks trivial and is the highest-leverage habit in the programme.
Without it there is no usefulness signal, no source pruning, and no basis for rule
promotion — the system generates output forever and improves at nothing.

---

## 13. Life integration

Four surfaces, deliberately few:

1. **Morning brief** — the primary surface. A state delta, not a dashboard dump. Answers:
   what changed, what it means for me, what to watch, what to do (often nothing).
2. **Critical alerts** — Telegram or push, governed by the Attention Covenant: material
   change only, deterministic trigger or strong multi-source confirmation. Every false
   alarm costs more trust than ten correct alerts earn.
3. **Weekly review** — the deliberate session where decisions are journaled and outcomes
   resolved. This is where the compounding happens.
4. **Ask on demand** — MCP or chat over live Atlas state (Queue 17). Read-only, with
   provenance IDs in every response, so an answer can always be traced to evidence.

**"No action" must be a first-class, well-formed output.** A system that always finds
something to say is a system that will be ignored within a month. The willingness to
report a quiet day is what makes the loud days credible.

---

## 14. Cost model

| Phase | Infrastructure | Models | Total |
| --- | --- | --- | --- |
| 0 | €0 (free tiers) | €10–30/mo | **€10–30/mo** |
| 1 | €20/mo VPS | €20–60/mo | **€40–80/mo** |
| 2 | €20/mo VPS | €40–120/mo | **€60–140/mo** |
| 3 | Hardware amortised + €10/mo | €10–40/mo (reasoning only) | **€20–50/mo** + capex |

Model spend is dominated by extraction volume, which is exactly the class that migrates
local first. Two controls keep it honest:

- **Deterministic code beats a model call** wherever it can do the job. Most ingestion,
  scoring, dedupe and policy work needs no model at all.
- **Per-run cost is recorded** in the run record, so cost per useful brief item is a
  measurable quantity rather than a surprise at the end of the month.

---

## 15. Programme risks

Ordered by probability, not by drama.

| Risk | Why it happens | Mitigation |
| --- | --- | --- |
| **The owner stops reading the brief** | Noise, or output that never changes a decision | Attention Covenant; daily usefulness marking; aggressive source pruning; permit quiet days |
| **Source sprawl** | Adding sources feels like progress | Blueprint §36 rule: do not expand sources until the small slice produces obvious daily value |
| **Inferred treated as fact** | A fluent explanation reads as certainty | Impact classification visible in every surface; fact / inference / speculation never rendered alike |
| **Model spend outruns value** | Agents multiply, everything gets an LLM call | Deterministic-first rule; per-run cost tracking; local migration of the FAST class |
| **Data loss** | Backups configured once, never tested | Quarterly restore test as a calendar obligation |
| **Personal data reaches the public repo** | A fixture built from real data during debugging | Commit-time rules in `SECURITY.md`; synthetic fixtures only; secret scanning as backstop |
| **Architecture erosion under agent velocity** | Agents optimise for the immediate task | CI boundary guards; one queue item at a time; ADR requirement for architectural change |
| **Silent quality drift** | Prompt changes improve prose, degrade extraction | Golden fixtures as CI gates |

---

## 16. Success metrics — and anti-metrics

### Success, by phase

- **Phase 0:** 30 consecutive daily cycles with no manual repair.
- **Phase 1:** ≥50% of briefs contain an item the owner marked useful; zero false `ACTION`
  alerts in a month.
- **Phase 2:** ≥50 resolved decisions; Brier score beats the base rate on ≥1 scenario
  family; ≥1 rule promoted from inferred to deterministic.
- **Phase 3:** FAST_MODEL fully local with no golden-fixture regression; L3 data reasoned
  over without leaving the perimeter.
- **Overall, the real one:** at least one decision the owner would not have made without
  Atlas, which proved correct — and at least one case where Atlas said "no action" and
  that was the right call.

### Anti-metrics — growth here signals failure, not progress

- number of sources;
- number of agents;
- number of world dimensions;
- brief length;
- lines of code.

Each of these can grow indefinitely while usefulness falls. If any is growing and the
usefulness rate is not, the correct response is to **remove**, not to add.

---

## 17. What to do next

1. Build Queue 01 against PostgreSQL 16 using the exact scope in `BUILD_QUEUE.md`.
2. Resolve later proposed ADRs only before the queue item each one gates.
3. Build Queue 02–14 as a single vertical slice. Resist every temptation to widen it.
4. Start the daily marking habit **the day the first brief exists**, not later. The
   feedback record cannot be reconstructed retroactively.
