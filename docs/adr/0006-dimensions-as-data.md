# ADR-0006 — World-state dimensions are data, not code

- Status: Proposed
- Date: 2026-08-28
- Supersedes / Superseded by: —

## Context

Blueprint §1.2 requires that the owner is modelled as a generic single-user profile and
that owner specifics never reach core domain code, so a multi-user product stays
possible. Blueprint §6.6 then enumerates world-state dimension keys that include
`geography.turkey_economy`, `geography.turkey_fx`, `geography.turkey_social_stress`,
`migration.eu` and `migration.us`.

These two requirements contradict each other. Those keys are not properties of the world;
they are properties of *this owner's* exposure to the world. A different owner based in
Lisbon with candidate geographies in Asia needs a different set, and would be forced to
either carry dead dimensions or patch core code.

The contradiction is not cosmetic. If dimension keys are a hard-coded enum, then adding a
geography is a code change with a migration, the World State engine's test fixtures are
owner-specific, and the "generic profile" claim in `PERSONAL_STATE.md` is false.

## Decision

Dimension keys are **rows, not an enum**.

A `world_state_dimension` registry table defines each dimension:

```
WorldStateDimensionDef
- key                  # e.g. "macro.liquidity", "geography.tr.fx"
- category             # macro | markets | crypto | energy | commodities |
                       # geopolitics | technology | regulation | geography |
                       # migration | climate
- scale_min, scale_max # default -3..+3
- direction_semantics  # what "rising" means for this dimension
- description
- enabled
- owner_scoped         # true when the dimension exists because of owner exposure
- geography_ref?       # ISO country/region code when owner_scoped
- created_at, retired_at?
```

Rules that follow:

1. **Core engine code never enumerates keys.** It iterates the enabled registry. A
   dimension is a value the engine handles, never a branch in the engine.
2. **Owner-scoped dimensions are derived from `GeographyState`.** When a country enters
   the owner's profile as `current_base`, `candidate`, `fallback` or `work_market`, the
   registry gains its geography dimensions from a template; when the country leaves the
   profile, the dimensions are **retired, not deleted** — history and provenance survive
   (A02).
3. **Keys use ISO codes for geography**: `geography.tr.fx`, not `geography.turkey_fx`.
   Machine-resolvable, and it makes the templating in rule 2 mechanical.
4. **Non-geographic dimensions are seeded**, not owner-derived: `macro.*`, `markets.*`,
   `crypto.*`, `technology.*`, `regulation.*`, `geopolitics.global` exist for every owner.
5. The V1 starting set stays ten dimensions (`WORLD_STATE.md`). The registry makes the
   set configurable; it does not license expanding it.

## Consequences

- Adding or removing a geography is a data change, not a deployment.
- World State fixtures become owner-independent: a replay fixture declares the registry
  it assumes, so golden tests are portable.
- Slight cost: the engine can no longer rely on a static type for keys. Mitigated by
  validating every key against the registry at write time, and by the registry being
  small and cached.
- `WorldStateDimension` rows keep referencing keys by string, as they already do; only
  the source of legitimacy changes.

## Enforcement

- Queue 06 acceptance gains: no dimension key literal appears in `packages/atlas/world_state`
  outside seed data and tests. A boundary test greps engine sources for the `geography.`
  and `migration.` prefixes.
- A world-state write whose key is absent from the enabled registry is rejected by the
  validator, not silently accepted.

## Alternatives considered

- **Keep the enum, accept owner-specificity.** Rejected: contradicts §1.2 and makes the
  claim of owner-genericity in `PERSONAL_STATE.md` untrue.
- **Two-tier: global enum plus owner extension table.** Rejected as needless: one registry
  with an `owner_scoped` flag expresses the same thing with one code path.
