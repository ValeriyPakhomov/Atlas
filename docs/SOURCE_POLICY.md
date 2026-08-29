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

Layers 1–3 are deterministic, versioned and authoritative; layers 4–5 only ever *propose*
a merge (ADR-0007). Layers 1–3 are implemented in `atlas.ingestion.idempotency`; the
proposal lifecycle lands with Queue 03.

**Scoping.** External ids are matched within their source — provider id spaces are
private, and two feeds both numbering an item `1` are not the same item. Canonical URL
and content hash are matched **globally**, because the same article reached through two
aggregators is one artifact, and identical wire copy run by six outlets is one artifact
six times. That global scope is what stops syndication from masquerading as
corroboration and inflating the credibility of a single claim: corroboration means two
*different* artifacts saying the same thing.

Multiple `RawItem` rows may legitimately merge into one `Event`. Re-ingesting the same
batch must not double event or narrative counts (A08, Queue 02–03 acceptance).

## The exposure gate

Before any model call, an item must name something the owner is actually exposed to —
an instrument held, a currency carried, a country with a role, an entity named in an
objective. The gate is a token trie over the owner's exposure set: free, offline and
deterministic. It is the largest cost reduction in the pipeline (`docs/COST_MODEL.md`
§2), but that is the smaller half of the argument — it is the same filter that keeps the
daily brief readable, so the cheap path and the good path are the same path.

Three rules bound it:

- **Nothing is dropped silently.** Every rejected item keeps a decision naming the
  exposure profile version it was judged against and what it failed to match. Those
  reasons are rendered, and correcting one is how the owner teaches Atlas.
- **The owner is never gated.** Anything the owner submitted is relevant by construction.
- **An empty profile admits everything.** Before Atlas knows the owner, gating would make
  the world look quiet rather than unknown.

## Adapter isolation

Source adapters implement one contract (`atlas.ingestion.contracts`):

```python
class SourceAdapter(Protocol):
    @property
    def descriptor(self) -> AdapterDescriptor: ...

    def fetch(self, window: FetchWindow, cursor: SourceCursor | None = None) -> FetchBatch: ...
```

Three deviations from the blueprint sketch, each deliberate:

- **The window is a parameter, not `now()`.** An adapter that reads the wall clock cannot
  be replayed. Passing the window in is what makes a re-read of 2026-03-11 reproducible
  (A02, A07).
- **`fetch` is synchronous.** Ingestion is a batch cycle, not a request path, and the
  persistence layer is synchronous SQLAlchemy. Concurrency, when a network adapter needs
  it, belongs to the cycle runner rather than to the contract.
- **The descriptor is part of the contract.** Atlas must be able to know a source's
  reliability class, tier, parse version and — critically — that it is
  `write_capable: Literal[False]`, without invoking it (ADR-0003).

A source that fails degrades its batch to an explicit incompleteness carrying the reason;
it never returns an empty batch that reads as a quiet day (A06). Only *typed* adapter
failures do this: any other exception is an Atlas defect and is allowed to escape, because
a bug and an outage must not leave the same record.

Platform quirks stay inside the adapter. If an upstream API changes, only its adapter
breaks — the domain model does not.

The concrete list of sources — with access mode, terms and what each is permitted to do —
is [`SOURCE_CATALOGUE.md`](SOURCE_CATALOGUE.md), backed by `atlas.ingestion.registry`.

V1 adapters: manual submission endpoint, MarketTwits-style feed, FRED/official macro,
market prices via the OpenBB adapter, crypto market data, general web/news research,
selected government and legal sources.

## Legal and operational rule

An open-source client library grants **no** right to redistribute the data it fetches
(ADR-0005, blueprint §33). Market data, news content and platform APIs each carry their
own terms. For a private single-user system ingestion can be broad, but the
architecture must not assume scraping a platform prohibits, and adapters must stay
replaceable so a licensing change is an adapter swap rather than a rewrite.
