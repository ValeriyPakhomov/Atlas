# Impact Engine

*Full implementation: Queue 09. Deterministic operators: Queue 08. Policies: Queue 11.*

The Impact Engine is Atlas's primary differentiator. It joins a `WorldStateDelta` to
the current `PersonalStateSnapshot` and answers: **what does this change mean for me?**

## Pipeline

```
WORLD DELTA -> Exposure Resolver -> Causal Rule Graph
                                      |-> deterministic impacts
                                      |-> research required?
                                            -> LLM causal synthesis
                                                 -> Impact validator -> IMPACT OBJECTS
```

## Exposure Resolver (deterministic)

Resolves which owner exposures a world change actually touches. Examples:

- *USD strengthening* → USD-denominated assets → TRY/EUR-denominated expenses →
  USD-linked income.
- *Turkey inflation rising* → current geography = Turkey → TRY cash exposure → local
  monthly burn → local income exposure → Turkey fortress score.
- *AI capability acceleration* → startup/product development → modelling/creative career
  exposure → software development cost → competitive pressure.

## Deterministic portfolio operators (Queue 08)

Pure functions: typed in, typed out, no network, fully unit-tested, explicit about
missing data.

```
net_worth()            liquid_net_worth()      asset_class_weights()
currency_weights()     geography_weights()     crypto_weights()
concentration_index()  runway_months()         monthly_cashflow_range()
scenario_mark_to_market()                      policy_breaches()
```

```python
def runway_months(liquid_assets: Money, monthly_burn: Money) -> Decimal:
    if monthly_burn.amount <= 0:
        raise ValueError("monthly burn must be positive")
    return liquid_assets.amount / monthly_burn.amount
```

An LLM never computes these (ADR-0004).

## Impact classification

Every impact is tagged with how it was derived, and the tag is visible to the owner:

| Tag | Meaning | Example |
| --- | --- | --- |
| `DIRECT_CALCULATED` | arithmetic on known positions | BTC −20% mark-to-market |
| `DIRECT_RULE` | deterministic rule plus measured data | TRY inflation raising local expenses |
| `INFERRED_CAUSAL` | model-synthesised causal link | AI progress increasing startup competition |
| `SPECULATIVE` | plausible, evidence still thin | war scenario indirectly affecting a city |

Fact, inference and speculation must never be presented as the same kind of claim.

## Priority and attention

A transparent composite, with every component normalised 0..1 and **stored
individually** so the ranking can be audited:

Priority measures how much an impact matters **if true**. Confidence is deliberately not
multiplied into priority (ADR-0008): a severe uncertain impact should route to `VERIFY`, not
disappear from the ranking.

```
priority = (severity^ws · exposure^we · urgency^wu)^(1/(ws+we+wu))
           × (1 + irreversibility)
```

Attention is a separate deterministic classification shared by impacts, briefs and alerts:
`ACTION | VERIFY | REVIEW | BACKGROUND | SUPPRESS`. There is no separate alert-severity
enum and no numeric expected-value-of-interruption model in V1.

## Policy interaction (Queue 11)

Policies are owner-authored constraints, not model recommendations — e.g. "liquid
runway ≥ 12 months", "crypto ≤ 25% of liquid net worth", "residence deadline alert ≥ 90
days", "no automated trading". Evaluation is pure deterministic code returning
`PASS | WARN | BREACH | UNKNOWN_DATA`. There is **no LLM override path**; a model may
explain a result, never change it.

`UNKNOWN_DATA` is a real, first-class result. It is never quietly reported as `PASS`.

## Acceptance (Queue 09)

- The BTC / TRY / rates / AI / migration fixture set produces the expected impacts.
- Inferred and calculated impacts are distinguishable in storage and in the UI.
- Every impact carries a causal chain back to evidence (A05).
- Every impact uses the single attention taxonomy from ADR-0008.
