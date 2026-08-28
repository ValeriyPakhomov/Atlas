# Source Policy

Not every source deserves equal weight. This policy makes that explicit and
deterministic, so a viral post cannot move World State the way a central-bank release can.

## Reliability classes

| Class | Description | Effect on state |
| --- | --- | --- |
| **A** | Official primary source: filing, central bank, regulator, statistical agency | May move World State directly with adequate materiality |
| **B** | High-quality wire or major financial publication | May move World State with corroboration |
| **C** | Specialist data provider or respected analyst | Contributes evidence; rarely decisive alone |
| **D** | Social media, aggregator, anonymous channel | **Signal radar only.** Triggers research; should rarely change World State alone |

MarketTwits and similar feeds are class D by default: valuable for *what to look at*,
never automatic ground truth.

## Anti-hype rule

One viral item cannot materially alter a high-level narrative unless source reliability
**and** event materiality justify it. Corroboration across independent sources raises
credibility; repeated republication of the same item does not (that is deduplication,
not evidence).

## Freshness and failure

Every source carries a `latency_class` and expected refresh interval. Staleness beyond
that interval is reported by `/health/data`, not hidden. A failed source degrades the
run explicitly and is recorded in the `RunRecord`; it never corrupts state and never
causes a silently substituted value (A06).

## Idempotency at ingestion

Deduplication layers, in order (blueprint §7.2):

1. exact external ID;
2. canonical URL;
3. normalised content hash;
4. near-duplicate semantic similarity;
5. event-level entity/time/topic matching.

Multiple `RawItem` rows may legitimately merge into one `Event`. Re-ingesting the same
batch must not double event or narrative counts (A08, Queue 02–03 acceptance).

## Adapter isolation

Source adapters implement one contract:

```python
class SourceAdapter(Protocol):
    name: str

    async def fetch(self, cursor: SourceCursor) -> FetchBatch: ...
```

Platform quirks stay inside the adapter. If an upstream API changes, only its adapter
breaks — the domain model does not.

V1 adapters: manual submission endpoint, MarketTwits-style feed, FRED/official macro,
market prices via the OpenBB adapter, crypto market data, general web/news research,
selected government and legal sources.

## Legal and operational rule

An open-source client library grants **no** right to redistribute the data it fetches
(ADR-0005, blueprint §33). Market data, news content and platform APIs each carry their
own terms. For a private single-user system ingestion can be broad, but the
architecture must not assume scraping a platform prohibits, and adapters must stay
replaceable so a licensing change is an adapter swap rather than a rewrite.
