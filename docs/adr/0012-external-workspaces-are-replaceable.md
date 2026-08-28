# ADR-0012 — External workspaces are replaceable surfaces

- Status: Proposed
- Date: 2026-08-28
- Supersedes / Superseded by: —

## Context

Generic assistant infrastructure has become commodity: multi-model chat, agent loops,
tool execution, MCP clients and transports, web research, email, calendar, tasks,
scheduled agents, local model hosting, document editing, semantic memory.

`odysseus-dev/odysseus` is a concrete instance. Verified at commit
`c9dd68d890a7c0ee0df9a0e351ce22aafd6c7c0f`: `LICENSE` is GNU AGPL v3 and the project
declares `AGPL-3.0-or-later`. Spot-checks confirm the audited characterisation —
qualitative memory is JSON-backed (`src/memory.py`, `data/memory.json`) with optional
vector retrieval (`src/memory_vector.py`, Chroma), plus MCP transports, CalDAV sync and a
scheduler.

The temptation is to adopt such a workspace as Atlas's runtime, UI or memory. That would
be a category error. Those systems are excellent at *interaction*; Atlas's value is
*persistent structured truth about one person over years*. A general agent loop selecting
tools is the opposite of a deterministic, replayable, idempotent state machine.

There is also a licence dimension: AGPL obligations follow the AGPL work. A protocol or
process boundary keeps them there.

## Decision

Atlas Core owns truth and intelligence. Every assistant, UI and agent runtime is a
**client** of a read-only surface:

```
ATLAS CORE — structured Postgres truth
  World / Personal / Impact / Scenario / Policy / Decision / Outcome
                      ↓
            READ-ONLY API + MCP
                      ↓
  ChatGPT · Claude · Odysseus · web · Telegram · future assistants
```

Binding properties:

1. **Removal test.** Removing any external workspace has *zero* effect on Atlas canonical
   state, replay, the daily cycle, forecasts, decisions or data integrity. If removing a
   client would break Atlas, the boundary has been violated.
2. **No client holds canonical state.** A workspace's own memory, notes or files are
   never a source of Atlas truth. Content flows into Atlas only through the manual-source
   endpoint or a trusted adapter, where it becomes a `RawItem` with provenance like any
   other input.
3. **No agent framework in the domain.** No workspace runtime, LangGraph, or agent library
   may appear in `packages/atlas/domain`, and none may be the canonical heartbeat.
   `run_atlas_cycle(as_of)` stays deterministic, idempotent and replayable (A07, A08).
4. **No AGPL source in Atlas.** Odysseus and comparable projects are reference
   architecture and optional external clients, reached over HTTP/MCP across a process
   boundary. Any future commercial arrangement requires legal review before relying on
   that boundary (ADR-0005).
5. **No external workspace is an execution path.** A workspace with privileged shell and
   filesystem tools and no complete sandbox must never sit on a path that moves money
   (ADR-0013).
6. **Atlas builds its own dashboard.** A generic AI workspace is chat-first; Atlas is
   state-, impact- and scenario-first. Queue 16 stays Atlas-owned.

## Consequences

- Queue 17 is reframed from "chat interface" to **read-only MCP server plus API surface**,
  consumable by several clients at once. No single chat UI can become load-bearing.
- Commodity integrations — email, calendar, tasks, browser, documents — are not rebuilt
  in Atlas. Where Atlas needs them later, they arrive through a protocol boundary.
- Atlas benefits from improvements in external assistants without inheriting their
  coupling, their licence, or their security posture.
- Cost: the read-only surface must be genuinely good, since it is the only way anything
  reaches a user. Every tool response carries provenance IDs so a client can cite.

## Enforcement

- A test asserts no import from an external workspace or agent framework in
  `packages/atlas`.
- Queue 17 acceptance gains an explicit removal test: with every external client
  disconnected, the daily cycle and a replay produce byte-identical results.
- Any adapter that ingests content from a workspace writes a `RawItem` with a source of
  record — never directly into a downstream entity.

## Alternatives considered

- **Adopt a workspace as the Atlas runtime and build engines as its tools.** Rejected: an
  LLM-driven tool loop cannot provide replay, idempotency or deterministic arithmetic, and
  it would put an AGPL runtime on the critical path.
- **Fork a workspace and strip it.** Rejected by ADR-0005 and by the licence boundary.
- **Build Atlas's own chat and email.** Rejected: commodity, and it delays the vertical
  slice that proves the intelligence is worth anything.
