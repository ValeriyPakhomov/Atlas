# Architecture Review — Cognitive Expansion and External Workspace Boundary

- Date: 2026-08-28
- Scope: final architecture review **before the first persistence migrations**
- Inputs: Blueprint v1; Queue 00 and ADRs 0001–0010; Constitution A01–A12; an
  `odysseus-dev/odysseus` source audit
- Status: review complete; reconciled before persistence — ADR-0010/0011 accepted,
  ADR-0012–0014 remain proposed; no production code written by this review

---

## A. Executive verdict

1. **The existing architecture survives this review.** Nothing in the proposed expansion
   contradicts A01–A12. Queue 00 needs no rewrite, and no Queue 00 boundary changes.
2. The expansion chain is **additive, not corrective** — it names capabilities the current
   architecture leaves undefined rather than ones it gets wrong.
3. But the chain is **mis-shaped as a pipeline**. World/Self/Goal are *state*; Causal is a
   *substrate* consulted at several points, not a stage; Forecast/Counterfactual/Options
   are *derivations*; Planning/Authority/Execution are *actuation*; Outcome/Meta-learning
   is the *loop closing back onto state and substrate*. Implementing it as a linear
   pipeline would produce a "causal service" that runs once per cycle — wrong.
4. **The one genuine gap is goals.** Current `Goal` is a to-do with a deadline. Both
   "opportunity" and "counterfactual" are *undefinable* without goals in canonical state:
   an opportunity is favourable **relative to something wanted**, and comparing options
   requires a criterion. This is the load-bearing addition. ADR-0011.
5. **`Forecast` is the highest value-per-byte addition in this review.** Storing owner
   prediction, Atlas prediction and outcome is a small table that enables learning which
   domains each is better at — and it is **impossible to reconstruct later**. Define now.
6. Organising principle for what must land before the first migration — the
   **reconstructability test**: reserve now only what cannot be recovered afterwards.
   Everything computable later from stored primitives can wait.
7. **`Opportunity` should not be an entity.** It is a *view* over `Impact` with goal
   linkage and capability gating. A separate entity duplicates provenance, priority and
   classification machinery. What *is* genuinely separate is the proactive **opportunity
   scan** — finding options implied by owner state and *unchanged* world state — and that
   is a later engine, not a schema change.
8. **`Constraint` and `AntiGoal` are rejected as entities.** A constraint is a `Policy`
   with a goal link; an anti-goal is an `Objective` with `direction = avoid`. Adding both
   would create overlapping concepts with one evaluator. This is ontology avoided.
9. **`Option` needs reservation, not implementation.** But `Decision` must record the
   alternatives considered from day one — "what did I choose *among*" is unreconstructable,
   and a decision journal without it cannot support regret or opportunity-cost analysis.
10. **Attention needs unification, and this is a real defect fixed by the pre-persistence
    reconciliation.** The sole taxonomy is `ACTION | VERIFY | REVIEW | BACKGROUND |
    SUPPRESS` across impacts, briefs and alerts.
11. Attention stays deterministic and separate from priority/confidence. Numeric
    expected-value-of-interruption modelling is deferred until owner behavioural data can
    support it without false precision.
12. **The causal graph is a later engine with one cheap change now**: make
    `Impact.causal_chain` a typed, normalised structure instead of free JSON, so edges can
    be extracted later without re-parsing prose. Building the graph before there are
    impacts to learn from is backwards.
13. **Strategic planning is deferred.** It is where over-engineering risk is highest and
    it overlaps commodity task tools. The Atlas-specific part is not the plan — it is the
    *replanning trigger* ("world state broke your plan's assumption"), which is a Watch
    over an externally held plan.
14. **Odysseus claims verified**, not taken on trust: HEAD is
    `c9dd68d890a7c0ee0df9a0e351ce22aafd6c7c0f`, `LICENSE` is GNU AGPL v3, declaration is
    `AGPL-3.0-or-later`; JSON-backed memory plus optional Chroma vectors, MCP transports,
    CalDAV and a scheduler all confirmed by spot-check.
15. **The proposed Odysseus boundary is correct and should be an ADR** — stated generally,
    since the principle outlives this particular project. ADR-0012.
16. **The autonomy ladder needs two corrections.** L2/L3 are not ordered (preparation does
    not require simulation), and a single global level wrongly puts reading market data
    and moving funds on one scale. Authority is `(domain, level, bounds, expiry)`. ADR-0013.
17. **L6 should be architecturally impossible, not merely prohibited.** The Gateway accepts
    an action only against a matching `(CapabilityGrant, Approval)` pair. A prohibition in
    prose survives until a refactor; a missing function signature does not.
18. **Trading: the hypothesis is right except at step 5.** A prepared order is one API call
    from being sent — so order preparation requires the Gateway to already exist as a
    separate boundary. And step 7 deserves a stronger bar than "much later": it should
    require *demonstrated evidence* that manual confirmation is what limits outcomes.
19. **The moat holds**, and it is not chat, agents, tools or integrations — all conceded as
    commodity. It is longitudinal structured point-in-time state, a decision-outcome ledger,
    personal causal rules, deterministic auditable arithmetic and replay. The data is the
    moat, and it is not transferable.
20. **Verdict: proceed.** The pre-persistence reconciliation accepted ADR-0010/0011,
    selected Neon PostgreSQL 16 in AWS Frankfurt, and made Queue 01's scope explicit.

---

## B. Architecture changes

### REQUIRED NOW — before the first migration

| # | Change | Why it cannot wait |
| --- | --- | --- |
| B1 | Every persisted field declares a sensitivity tier (ADR-0010) | Retrofitting a tier onto every model touches every file and every call site; the enforcement point must exist before the first field does |
| B2 | Queue 01 `Objective` and `Preference`; future `Policy.objective_id?` contract (ADR-0011) | Objectives are temporally versioned. A decision made in Queue 12 must be judgeable against what the owner wanted *then*; Policy is not created early as a placeholder |
| B3 | Minimal `ForecastQuestion`, `ForecastPrediction`, `ForecastResolution` ledger | Owner predictions cannot be backfilled. Store primitives; derive Brier/calibration later |
| B4 | Unify attention into one model across impacts and alerts | Three competing taxonomies would be implemented into Queue 09 and Queue 15 separately and then have to be reconciled across both |

### RECOMMENDED NOW — cheap, and expensive later

| # | Change | Why |
| --- | --- | --- |
| B5 | `Impact.causal_chain` as a typed structure, not free JSON | Enables later causal-graph extraction without re-parsing stored prose |
| B6 | `Impact.objective_refs[]` | Makes the opportunity view possible with no new engine |
| B7 | `Decision.considered_options` recorded from day one | Alternatives not recorded are gone; regret and opportunity cost become uncomputable |
| B8 | Derived records store the artefact versions in force (ADR-0014) | Without it, promoting one rule silently rewrites the meaning of every past impact |
| B9 | `LLMProviderPort` request/response contract defined in vocabulary now | Vendors differ on structured output; a lowest-common-denominator typed contract prevents a vendor's shape leaking into engines |
| B10 | Reserve vocabulary only: `Option`, `ActionProposal`, `CapabilityGrant`, `Approval`, `ExecutionRecord`, `Resource`, `Counterfactual`, `Plan` | Documented reservation is a boundary; an empty table is an invitation |

### DEFERRED

- **Opportunity scan engine** — proactive discovery over unchanged world state. Needs
  Impact and Personal State working first (post-Queue 09).
- **Option / Counterfactual engine** — requires the portfolio engine (08), impact engine
  (09) and scenarios (10) all operational.
- **Causal graph construction** — should emerge from accumulated impacts, not precede them.
- **Strategic plan graph** — research; overlaps commodity tooling. Revisit only if the
  replanning trigger proves insufficient.
- **Resource model beyond Personal State** — time, attention, skills and network capital
  are not measurable enough to be canonical yet. Reserved as concepts.
- **Semantic memory supersession** — becomes a *selection criterion* for Queue 18 rather
  than a design task now.
- **Proposer/Challenger/Judge on every decision** — the blueprint already has Challenger
  and Judge for scenarios. Extending to all decisions triples model cost per decision;
  apply only to material ones.

### REJECTED

| Rejected | Reason |
| --- | --- |
| `Opportunity` as an entity | A view over `Impact`; a separate entity duplicates provenance, priority, classification |
| `Constraint` as an entity | A `Policy` with a goal link. Two concepts, one evaluator = permanent ambiguity |
| `AntiGoal` as an entity | An `Objective` with `direction = avoid` |
| Utility functions and trade-off rates | Elicitation is unreliable; a bad number propagates false precision into every ranking (A12) |
| Plan graph as canonical V1 state | Over-engineering; commodity tools do this adequately |
| Any agent framework in the domain | A01, A07 |
| Adopting an external workspace as runtime, UI or memory | ADR-0012 |
| Treating the expansion chain as a linear pipeline | Mis-models causal reasoning as a stage |

---

## C. ADR outcomes

Four records settle questions that would otherwise be decided by accident. ADR-0011 is
Accepted by the reconciliation; ADR-0012–0014 remain Proposed until their later gates.

| ADR | Title | Why it earns its place |
| --- | --- | --- |
| [0011](../adr/0011-goals-are-owner-authored-state.md) | Objectives, preferences and constraints are owner-authored canonical state | Opportunity and counterfactual are undefinable without owner intent; and this is the one domain where the model must never author |
| [0012](../adr/0012-external-workspaces-are-replaceable.md) | External workspaces are replaceable surfaces | Answers the Odysseus question as a durable principle; carries the removal test and the AGPL boundary |
| [0013](../adr/0013-autonomy-ladder-and-execution-gateway.md) | Autonomy ladder and the Execution Gateway boundary | Extends ADR-0003 without weakening it: describes safe execution so it is never improvised |
| [0014](../adr/0014-auditable-self-improvement.md) | Self-improvement is proposed, validated, approved and versioned | Governance must exist before the mechanism, or auto-promotion becomes permanent by default |

**Deliberately not written:** an ADR for the counterfactual/options model. It is a later
engine; what is needed now is vocabulary reservation and one column on `Decision`. Writing
an ADR for an engine several queue items away would be documentation volume, not a
decision.

---

## D. Queue 01 schema impact

The **reconstructability test** decides each case: *if this is not recorded from the
beginning, can it be recovered later?* If no, define now. If yes, defer.

| Object | Verdict | Migration-cost reasoning |
| --- | --- | --- |
| **Objective** | `DEFINE NOW` | Temporally versioned. Judging a past decision needs the objectives active at that time; unrecoverable afterwards. Two columns + interval, cheap |
| **Preference** | `DEFINE NOW` | Ordinal pairs only. Tiny table. Same recoverability argument |
| **Forecast ledger** | `DEFINE NOW` | Owner/Atlas predictions and provenance-backed outcomes are unreconstructable. Brier/calibration remain derived analytics |
| **Constraint** | `REJECT` | Is a `Policy` with `objective_id?`. Adding one nullable column instead of an entity |
| **AntiGoal** | `REJECT` | `Objective.direction = avoid` |
| **Opportunity** | `REJECT` (as entity) | A view over `Impact` given `objective_refs[]`. Requires B6, not a table |
| **Option** | `RESERVE CONCEPT ONLY` + one column | Engine deferred, but `Decision.considered_options` must be recorded from day one (B7) |
| **Counterfactual** | `DEFER` | Derived from Option plus engines that do not exist. Nothing to reserve beyond Option |
| **Resource** | `RESERVE CONCEPT ONLY` | Cash, liquidity and geography are already in Personal State. Time, attention, skills and network capital would be empty columns inviting speculative use |
| **Plan / PlanStep** | `DEFER` | Research. Adding tables now yields an unused schema and pulls Atlas toward task management |
| **ActionProposal** | `RESERVE CONCEPT ONLY` | No execution in V1. `Decision(type=PREPARE)` is the precursor. An empty table is an invitation (ADR-0013) |
| **CapabilityGrant** | `RESERVE CONCEPT ONLY` | Belongs to the Gateway's authority model, not Atlas Core |
| **Approval** | `RESERVE CONCEPT ONLY` | Same |
| **ExecutionRecord** | `RESERVE CONCEPT ONLY` | Explicitly lives in the **Gateway's** schema, never Atlas Core's. Atlas reads it back as an external observation with provenance |

### Queue 01 persistence contract

| Object | Change |
| --- | --- |
| all Queue 01 entities | Every column declares maximum/default tiers; relevant values carry effective tier (ADR-0010) |
| owner intent | `Objective` and `Preference`, with accepted active point-in-time authority and cycle rejection |
| forecast ledger | `ForecastQuestion`, immutable `ForecastPrediction`, provenance-backed `ForecastResolution`; no forecast engine |

`Policy.objective_id?` and derived-record artifact-version references remain binding future
contracts and are implemented with their owning later queue items, not as Queue 01
placeholder tables.

### Changes to objects created by later queue items — specified now so they are built right

| Object | Queue | Change |
| --- | --- | --- |
| `Impact` | 09 | `objective_refs[]`; typed `causal_chain`; unified `attention_class`; components stored individually (ADR-0008) |
| `Decision` | 12 | `considered_options`; `objectives_active_at_decision[]` |
| `Alert` | 15 | Unified `attention_class` replacing the separate severity enum |

---

## E. Queue 00–19 diff

Only what changes. Unchanged items are omitted deliberately.

| Queue | Change |
| --- | --- |
| 00 | **Unchanged.** No boundary is modified |
| 01 | **Extended and bounded:** ingestion foundation plus `Objective`, `Preference`, the three-table Forecast ledger and sensitivity infrastructure. No future-engine placeholder tables |
| 02–08 | **Unchanged** |
| 09 | **Extended:** objective linkage, typed causal chain and the reconciled five-class attention taxonomy in ADR-0008 |
| 10–14 | **Unchanged** |
| 15 | **Reframed:** Atlas owns alert semantics — impact, confidence, suppression, attention policy. Delivery channels are replaceable adapters. Uses the unified attention model, not a separate severity enum |
| 16 | **Unchanged, and explicitly confirmed:** Atlas builds its own state/impact/scenario-first dashboard. No external workspace UI |
| 17 | **Reframed:** from "MCP / chat interface" to **read-only MCP server + API integration surface**, consumable simultaneously by ChatGPT, Claude, Odysseus, web and Telegram. Acceptance gains the ADR-0012 removal test |
| 18 | **Reframed:** from "integrate Mem0" to a **comparative architecture checkpoint** — pgvector-native, Mem0, Letta/MemFS, Lethe and whatever is mature at that time. Selection criteria include formal supersession semantics (current / outdated / superseded / temporary / preference / changed preference / lesson / disproven lesson). No implementation is chosen now |
| 19 | **Unchanged.** Quant Lab stays last |

### Beyond V1 — sequenced, not scheduled

Kept off the numbered queue so the V1 slice is not diluted:

- Opportunity scan engine (proactive discovery)
- Option / Counterfactual engine
- Causal graph extraction from accumulated impacts
- Replanning trigger (a Watch over an externally held plan)
- Execution Gateway — **a separate system**, requiring an ADR that supersedes ADR-0003

---

## F. Odysseus integration decision

Verified at `c9dd68d890a7c0ee0df9a0e351ce22aafd6c7c0f`, AGPL-3.0-or-later.

| Area | Build Atlas | Borrow pattern | External Odysseus | Reject |
| --- | --- | --- | --- | --- |
| Agent runtime | — | ✓ typed graph shape | ✓ optional workspace | ✗ as Atlas runtime or heartbeat |
| MCP | ✓ Atlas as **server** (Queue 17) | ✓ transport patterns | ✓ as client | ✗ Atlas as MCP client dependency |
| Local models | ✓ provider port | ✓ hosting patterns | ✓ as testing cockpit | ✗ as Atlas inference path |
| Research | — | ✓ research-loop patterns | ✓ external research lab | ✗ as system of record |
| Email | — | — | ✓ | ✗ rebuilding in Atlas |
| Calendar | — | — | ✓ | ✗ rebuilding in Atlas |
| Tasks | — | — | ✓ | ✗ rebuilding in Atlas |
| Memory | ✓ canonical Postgres | ✓ extraction patterns | ✓ its own workspace memory | ✗ JSON/vector memory as Atlas truth |
| UI | ✓ Queue 16, state-first | — | ✓ as one more client | ✗ as canonical Atlas dashboard |
| Scheduler | ✓ `run_atlas_cycle` | ✓ trigger patterns | ✓ auxiliary jobs | ✗ as canonical heartbeat |
| Security | ✓ tiers, gateway, policy | ✓ prompt-injection hardening | — | ✗ its threat model as Atlas's |
| Execution | ✓ separate Gateway (later) | — | — | ✗ **any** financial execution path through a workspace with privileged local tools |

**Licence posture:** reference architecture and optional external client only. No source
copied. Protocol/process boundary preserved. Any future commercial arrangement requires
legal review before relying on that boundary — an engineering boundary is not a legal
opinion.

---

## G. Autonomy / execution matrix

Atlas V1 defaults to **L0–L1 in every domain**. L2 simulation is pure Core computation and
does not require the Execution Gateway. L3 preparation requires the Gateway contract and
boundary; L4–L5 operate in the Gateway; L6 is unsupported.

| Domain | Max level | Required approval | Notes |
| --- | --- | --- | --- |
| Research / ingestion | L1 | none | Reading is the product. Rate limits and source terms apply |
| Files (Atlas's own artefacts) | L1 | none | Briefs, exports, reports. No filesystem access outside its own storage |
| Email | L3 | per message | Draft only. Sending is never bounded-automatic — an email is irreversible and reputational |
| Calendar | L4 | per action, or L5 within a grant | Lowest-stakes domain; reversible; a plausible first L5 candidate |
| Purchases | L4 | per action, hard value cap | Never L5. A recurring purchase is a subscription the owner should set up themselves |
| Legal / residency submissions | L3 | **owner submits personally** | Never above L3, ever. Misfiling carries consequences Atlas cannot assess or remedy |
| Portfolio actions (rebalance) | L4 | per action | L5 only under §H's evidentiary bar |
| Trading | L4 | per order | See §H |
| Wallet / on-chain actions | L3 | **owner signs personally** | Atlas never holds keys at any level. Irreversible by construction |

Two rules cut across the table: **anything irreversible caps at L3** (prepare, never
transmit), and **every grant expires** — the L5 failure mode is a policy written once
against a world that then changed.

---

## H. Trading verdict

The hypothesis was: 1–4 yes; 5 likely yes; 6 possibly via separate infrastructure; 7 much
later and heavily constrained; 8 no. Assessment: **broadly right, with one correction and
one sharpening.**

| # | Capability | Verdict | Reasoning |
| --- | --- | --- | --- |
| 1 | Market intelligence | **Yes — core** | This is the product |
| 2 | Portfolio analysis | **Yes — core** | Deterministic operators, Queue 08. The highest-value financial output |
| 3 | Strategy proposals | **Yes, with framing** | As `REVIEW_ALLOCATION` decisions with explicit uncertainty. Never as signals |
| 4 | Paper trading | **Yes — L2** | Pure computation, touches nothing external. Genuinely useful: it is how a proposal is evaluated before it is trusted |
| 5 | Order preparation | **Yes — but only after the Gateway exists** | *Correction to the hypothesis.* A prepared order is one API call from being sent. If preparation lives in Atlas Core, the remaining distance to execution is a single line of code written under time pressure. Preparation must happen **inside** the Gateway boundary, from a proposal Atlas Core emits |
| 6 | Confirmed execution | **Yes — L4, separate infrastructure** | Per-order approval, idempotency key, hard value cap, full audit in the Gateway's schema. Requires an ADR superseding ADR-0003 |
| 7 | Policy-bounded execution | **Requires evidence, not merely time** | *Sharpening.* "Much later" implies it is eventually inevitable. For an individual it may have **no upside at all**: you are not latency-sensitive, you make a handful of decisions a month, and the tail risk of an automated action against a changed world is unbounded. The bar should be a **demonstrated, measured case that manual confirmation is what limits outcomes** — from the owner's own calibration data. If three years of data show confirmation delay costs nothing, 7 should stay permanently off. Rebalancing is the only plausible candidate, and even there the gain is small |
| 8 | Autonomous discretionary trading | **No — architecturally impossible** | Not a policy prohibition. The Gateway has no code path accepting an action without a matching `(CapabilityGrant, Approval)` pair |

**Standing constraint at every level:** Atlas Core holds no seed phrases, private keys,
withdrawal secrets or unrestricted broker authority. Credentials are read-only with
trading and withdrawal disabled at the provider until the Gateway exists — and even then,
they live in the Gateway, never in Core.

Worth restating plainly, because it shapes what "trading support" should even mean: Atlas
will not produce alpha. Its financial value is exposure awareness, risk and concentration
discipline, regime awareness, removal of behavioural error, and runway management
(`PROGRAM.md` §2). Execution capability adds convenience to that, not edge — which is
precisely why the evidentiary bar in row 7 is the right posture rather than an obstacle.

---

## I. Moat analysis

Assume every generic assistant acquires memory, browser, email, calendar, agents, MCP,
computer use and local models. **All conceded.** None is Atlas's moat, and building any of
them would be a mistake.

What remains, and why it is hard to copy:

**Longitudinal structured point-in-time state.** An assistant remembers conversations. It
cannot answer "what was my currency exposure on 3 March, and what did I believe about
liquidity then" — because it never stored that as versioned relational state with validity
intervals. This is not a capability gap that a better model closes; it is a data model
that must have been running for months.

**A decision–outcome ledger with calibration.** Requires deliberately recording what was
believed *before* outcomes are known. No assistant has the mechanism or the incentive, and
it cannot be reconstructed from chat history because the counterfactual was never written
down.

**Personal causal rules.** Generic models learn population-level regularities. Atlas's rule
promotion (ADR-0014) learns *this owner's* regularities from *this owner's* history, and
stores them as auditable deterministic code rather than weights.

**Deterministic, auditable arithmetic.** Assistants will remain probabilistic about
numbers. Runway, concentration and policy breach are not opinions.

**Replay.** Re-running a past decision under improved logic — structurally impossible
without append-only provenance and injected time. This is the capability that makes
"is Atlas actually getting better?" an answerable question.

**The moat is the accumulated data, and it is not transferable.** Eighteen months of one
person's structured state, decisions and resolved outcomes cannot be bought, imported or
prompted into existence. A vendor could build the same architecture — and would still start
at day zero on this owner's history.

Two honest qualifications. First, everything above is worth nothing if the system is not
used: an unread brief accumulates no decisions and therefore no moat. Second, the moat
compounds slowly and invisibly for the first several months, which is exactly when the
temptation to add sources and features is strongest. The discipline in `PROGRAM.md` §16 —
the anti-metrics — is what protects it.

---

## J. Next action

`PROCEED TO QUEUE 01`

The prerequisites are resolved by the pre-persistence reconciliation:

1. ADR-0010 and ADR-0011 are Accepted with their amendments.
2. Managed production PostgreSQL is Neon PostgreSQL 16 in AWS Frankfurt
   (`eu-central-1`); local development/tests use Docker PostgreSQL 16.
3. `DATA_MODEL.md` and `BUILD_QUEUE.md` define the same bounded Queue 01 scope.

ADRs 0006, 0007, 0008, 0009, 0012, 0013 and 0014 block later queue items, not this one.
They can be accepted at leisure, in this order of urgency: 0007 (before Queue 03), 0006
(before Queue 06), 0008 (before Queue 09), 0009 (before Queue 10), 0012 (before Queue 17),
0014 and 0013 (before any promotion or execution work exists).

No production feature code was written by this review. Queue 01 may now start directly.
