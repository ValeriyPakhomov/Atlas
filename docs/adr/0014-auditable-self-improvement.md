# ADR-0014 — Self-improvement is proposed, validated, approved and versioned

- Status: Proposed
- Date: 2026-08-28
- Supersedes / Superseded by: —

## Context

Atlas is meant to get better over years. `PROGRAM.md` §3 describes how: scenario
calibration, decision retrospectives, promotion of repeatedly-confirmed
`INFERRED_CAUSAL` impacts into deterministic `DIRECT_RULE` code, source-reliability
learning, and prompt improvement.

That is genuine self-modification. A system that silently rewrites its own rules is
unauditable by construction: a decision made last month cannot be explained if the rules
that produced it have since changed without a record. That directly contradicts A05
(provenance) and A07 (replay).

The governance has to exist before any of the mechanism does, because retrofitting an
approval lifecycle onto a promotion path that already runs is how "temporary" auto-promotion
becomes permanent.

## Decision

Everything Atlas learns follows one lifecycle, whatever the artefact:

```
candidate  →  validated  →  owner-approved  →  shadow  →  active  →  (demoted | superseded)
```

Applies to: causal rules, policies, source reliability weights, prompt versions and
scaffold changes. Not to ordinary data — an updated balance is state, not learning.

### Stages

1. **Candidate.** Generated from evidence: N confirmed observations, a calibration
   result, a measured extraction failure. The generating evidence is stored with the
   candidate; a candidate without evidence is rejected.
2. **Validated.** Replayed against history: would this rule have improved past outcomes?
   A candidate that does not improve on the golden and calibration sets never reaches the
   owner. This is deterministic and is where most candidates die.
3. **Owner-approved.** Explicit, per-artefact, recorded with a timestamp. **No blanket
   approval, no auto-approval threshold, no "approve all similar".**
4. **Shadow.** The approved artefact runs in parallel for a configured number of cycles.
   Its outputs are recorded and compared but **do not affect** briefs, alerts, decisions
   or state. This catches the rule that validated well on history and behaves badly on
   live data.
5. **Active.** Versioned, with a diff against what it replaced, an effective-from
   timestamp, and the run in which it activated.
6. **Demoted or superseded.** Any active artefact can be demoted. Demotion is a new
   version, never a deletion — history that was produced under it must stay explicable.

### Replay integrity

Every derived record stores the **artefact versions in force when it was produced**. A
replay of a past `as_of` uses those versions, not current ones. Without this, promoting a
single rule silently rewrites the meaning of every past impact, and the decision journal
becomes fiction.

### Scope limits

- **Atlas never modifies its own architecture, ADRs, boundaries or schema.** Learning
  operates on rules, weights and prompts — never on the constitution.
- **Objectives and preferences are excluded** — those are owner-authored (ADR-0011).
- **Promotion never crosses the deterministic/model line in the wrong direction.** A rule
  may be promoted from inferred to deterministic; nothing is ever demoted from
  deterministic code into model judgement.

## Consequences

- The compounding advantage in `PROGRAM.md` §3.3 becomes real and auditable: over time a
  meaningful share of Atlas's reasoning is deterministic rules derived from the owner's own
  history, each with a provenance trail back to the observations that produced it.
- Approval is a genuine cost on the owner's attention. Mitigated by stage 2: only
  candidates that demonstrably improve past outcomes are ever surfaced.
- Storing artefact versions on derived records costs a column and makes replay honest.

## Enforcement

- A test asserts no artefact reaches `active` without a stored owner approval.
- A test asserts a replay for a past `as_of` uses the artefact versions recorded on the
  run, not the current ones.
- A test asserts shadow-stage output never reaches a brief, alert or decision.

## Alternatives considered

- **Auto-promote above a confidence threshold.** Rejected: the threshold becomes the
  system's real governance, and it is set by the same machinery it governs.
- **Fine-tune a model on owner history instead.** Rejected: opaque, non-auditable,
  contradicts A05, leaks personal data into weights, and must be redone at every model
  upgrade (`PROGRAM.md` §3).
- **Approve categories rather than artefacts.** Rejected: a category approval is a blanket
  approval with extra steps.
