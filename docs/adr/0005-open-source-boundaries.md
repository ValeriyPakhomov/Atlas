# ADR-0005 — Upstream projects are consumed at a boundary, never forked

- Status: Accepted
- Date: 2026-08-28
- Supersedes / Superseded by: —

## Context

The blueprint audits seven upstream projects (§3, §38). Forking any of them makes
Atlas the maintainer of someone else's domain model and licence obligations, and
couples Atlas's core loop to upstream churn. OpenBB in particular is AGPL-3.0, which
deserves a clean architectural boundary before any commercial question arises.

## Decision

Atlas defines its own ports. Upstream code is reached through adapters, and upstream
*patterns* may be adapted with attribution. Atlas is never a fork.

| Upstream | Licence (verify at pin) | Strategy | Boundary |
| --- | --- | --- | --- |
| OpenBB | AGPL-3.0 | Borrow as data layer | `MarketDataPort`; OpenBB types never leave the adapter (Queue 04) |
| TradingAgents | Apache-2.0 | Adapt orchestration patterns | researcher → synthesis → challenge → judge graph shape only |
| FinRobot | Apache-2.0 | Adapt compute/provenance principles | typed operators, provenance on calculated outputs |
| AI Hedge Fund | MIT | Adapt run-cycle philosophy | `run_atlas_cycle` heartbeat; **no** execution code |
| Qlib | MIT | Defer | Quant Lab phase, Queue 19; not on the V1 critical path |
| Mem0 | Apache-2.0 | Borrow, optional | `SemanticMemoryPort`, non-authoritative per ADR-0002 |
| Open Deep Research | MIT | Adapt research-loop patterns | research graph never becomes the system of record |

Explicit prohibitions: no ticker-centric or trader-persona assumptions, no automatic
BUY/SELL semantics, no graph whose primary output is a trade, no research agent
holding canonical state.

### Mandatory record before copying any code

Nothing is copied without recording, in `THIRD_PARTY_NOTICES.md`: upstream repository,
**exact commit SHA**, upstream file path, licence at that SHA, the Atlas file using it,
and the modifications made. Licences must be re-verified at the pinned SHA rather than
trusted from this table.

### Software licence ≠ data rights

An open-source client library grants no right to redistribute the data it fetches
(§33). Market data, news content and platform APIs each carry their own terms. Adapters
must therefore stay replaceable, and no core architecture may assume scraping that the
platform prohibits.

## Consequences

- More interface code than direct SDK use, and the freedom to replace any provider.
- AGPL exposure stays confined to a process/service boundary, keeping future licensing
  options open without a rewrite.
- `THIRD_PARTY_NOTICES.md` is maintained from day one, before there is anything to record.

## Enforcement

- Queue 04 acceptance: OpenBB types do not leak outside the adapter package, and a
  provider failure surfaces as a typed Atlas error.
- Boundary tests deny `openbb`, `mem0`, `qlib`, `langchain` and `langgraph` imports
  inside `packages/atlas/domain`.
- Dependency review rejects any new upstream import that lacks an entry in
  `THIRD_PARTY_NOTICES.md`.

## Alternatives considered

- **Fork OpenBB and strip it down.** Rejected: inherits a different domain model, an
  AGPL obligation and a large maintenance surface.
- **Vendor small utilities by copy-paste without records.** Rejected: creates
  untraceable licence obligations. Copying is permitted only with the record above.
