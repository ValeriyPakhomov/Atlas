# Third-Party Notices

Maintained from day one per ADR-0005 and blueprint §32.

## Copied or adapted source code

**None yet.** No upstream source has been copied or adapted into Atlas.

Before any code is copied or adapted, add a row here and verify the licence **at the
pinned commit SHA** — not from documentation, and not from the table below.

| Upstream repo | Commit SHA | Upstream path | Licence at SHA | Atlas file | Modifications |
| --- | --- | --- | --- | --- | --- |
| — | — | — | — | — | — |

## Referenced projects (architecture references, no code copied)

Licences observed at blueprint authoring time and **must be re-verified before any
code reuse**.

| Project | Licence observed | Relationship to Atlas |
| --- | --- | --- |
| [OpenBB](https://github.com/OpenBB-finance/OpenBB) | AGPL-3.0 | Consumed behind `MarketDataPort`; no code copied. AGPL requires a clean service/library boundary and legal review before any closed commercial distribution. |
| [TradingAgents](https://github.com/TauricResearch/TradingAgents) | Apache-2.0 | Orchestration *patterns* only |
| [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) | Apache-2.0 | Deterministic-compute and provenance *principles* only |
| [AI Hedge Fund](https://github.com/virattt/ai-hedge-fund) | MIT | Run-cycle/ledger *philosophy* only; no execution code |
| [Qlib](https://github.com/microsoft/qlib) | MIT | Deferred to Queue 19 |
| [Mem0](https://github.com/mem0ai/mem0) | Apache-2.0 | Optional semantic memory behind `SemanticMemoryPort` |
| [Open Deep Research](https://github.com/langchain-ai/open_deep_research) | MIT | Research-loop patterns only |

## Runtime dependencies

Python dependencies are declared in `pyproject.toml` and resolved by `uv`. Their
licences are the licences of the published distributions.

## Data rights are separate from code licences

An open-source client library grants no right to redistribute the data it retrieves.
Market data, news content and platform APIs each carry independent terms
(ADR-0005, blueprint §33).
