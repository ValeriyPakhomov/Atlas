# Atlas Telegram surface (Queue 15)

An output adapter for alerts. Not yet implemented.

Severities (blueprint §21):

| Severity | Routing |
| --- | --- |
| `INFO` | store and dashboard only |
| `IMPORTANT` | included in the next brief |
| `CRITICAL` | immediate push |

`CRITICAL` requires a deterministic trigger criterion or strong multi-source
confirmation — never a single class-D item.

Every alert states: what happened, why Atlas believes it, which exposure is affected,
confidence, source links, and **whether immediate action is actually required**.
Duplicate alerts are suppressed (Queue 15 acceptance).

This is an output surface only. It never mutates canonical state, and it is read-only
with respect to external systems (ADR-0003).
