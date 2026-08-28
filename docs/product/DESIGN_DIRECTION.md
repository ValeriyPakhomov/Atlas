# Atlas Design Direction

Atlas should feel **intelligent, calm, precise, private, serious and restrained** — an
instrument, not an app.

Explicitly avoided: crypto-dashboard neon, Bloomberg density, generic SaaS card grids, AI
purple gradients, glassmorphism, cyberpunk, gamification, productivity-app cheer.

The nearest references are institutional research publications and premium operating
systems: quiet surfaces, strong typographic hierarchy, colour used sparingly and only for
meaning. Nothing is copied from any specific product.

---

## 1. The organising idea

> **Typography carries epistemics; colour carries direction; weight carries certainty.**

Three channels, three jobs, no overlap. Once the owner learns them, every screen reads
without a legend. This is the whole visual system; everything below is implementation.

---

## 2. Typography

Three families, each meaning something:

| Role | Family | Carries |
| --- | --- | --- |
| **Interpretation** | Serif (a text serif such as Source Serif / Charter class) | Atlas's own reasoning — the Atlas view, causal explanations, retrospectives |
| **Interface** | Neutral grotesque (Inter class) | Labels, navigation, controls, headings |
| **Measurement** | Monospace with tabular figures (JetBrains Mono / IBM Plex Mono class) | Every number: scores, probabilities, currency, dates, deltas, counts |

The serif is the load-bearing choice. It marks the boundary between *what Atlas measured*
and *what Atlas thinks*, so the owner never mistakes one for the other. It is also what
keeps Atlas from reading as a dashboard.

**Rules.** Numbers are always mono and always tabular — a column of figures must align.
Never set a number in the serif. Never set Atlas prose in the interface font. Scale is a
modest ramp (12 / 13 / 15 / 18 / 24 / 32); a big number earns its size by being the
answer, not by being a number.

## 3. Colour

Near-monochrome by default. Colour is reserved and rare; a screen where colour appears
three times is a screen where those three things matter.

### Surfaces and ink

| Role | Light | Dark |
| --- | --- | --- |
| Surface | `#fbfbfa` | `#141413` |
| Raised surface | `#ffffff` | `#1c1c1a` |
| Hairline | `#e4e3df` | `#2c2c29` |
| Ink primary | `#141413` | `#f5f5f2` |
| Ink secondary | `#57564f` | `#a3a29a` |
| Ink muted | `#8a8880` | `#74736c` |

Warm neutrals, not blue-grey. One elevation level: hairline borders, **no shadows, no
glass**.

**One atmospheric device is permitted: a tonal ground.** A single-hue, very-low-chroma
vertical gradient on the page background — never on cards, never behind data. Resolved
from reference review 2026-08 (§13): the distinction that matters is **material versus
lighting**. Lighting — glass, blur, glow, photographic grounds — requires something to
light, and that something becomes decoration; it also destroys the contrast guarantee,
because text over a photograph has variable legibility by definition. A tonal field is
material: it gives depth without introducing objects that float.

### Semantic colour — validated, not chosen by taste

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| Favourable | `#2a78d6` | `#3987e5` | Direction of an impact or driver in the owner's favour |
| Adverse | `#eb6834` | `#d95926` | Direction against |
| Attention (`ACTION` only) | `#e34948` | `#e66767` | The single interrupting class, nothing else |

**Favourable is blue, not green.** Measured with the palette validator: green↔red separates
at ΔE 6.9 under deuteranopia — inside the 6–8 floor band, legal only with secondary
encoding. Blue↔orange separates at **ΔE 24.7 light / 26.8 dark**, passing contrast in both
modes. It also avoids the green/red trading-terminal cliché. Two reasons, one answer.

Direction is *never* carried by colour alone regardless: an arrow glyph and a word always
accompany it.

### Categorical — scenarios only

The only categorical use in Atlas. Fixed slot order, never cycled:

| Slot | Light | Dark |
| --- | --- | --- |
| 1 | `#2a78d6` | `#3987e5` |
| 2 | `#eb6834` | `#d95926` |
| 3 | `#1baf7a` | `#199e70` |
| 4 | `#eda100` | `#c98500` |
| 5 | `#e87ba4` | `#d55181` |

Validated on the adjacent pairlist (a stacked probability bar is adjacent-only): worst CVD
ΔE 9.1 light / 8.4 dark; worst normal-vision ΔE 19.6 / 19.3. Slots 3–5 warn on light-mode
contrast, which obligates the direct labels the scenario bar already carries. Five slots is
the cap, matching the five-scenario maximum per set.

**Unassessed probability mass is not a slot.** It renders as a 45° hatch on the neutral
hairline colour — visibly *not a scenario*, which is the honest representation
(ADR-0009).

### What colour never does

Never encodes uncertainty. Never encodes magnitude. Never distinguishes navigation.
Never brands a section. Never escalates because there is more news.

## 3b. Measured versus not measured — the stroke rule

Adopted from reference review 2026-08. A single graphical convention, applied everywhere a
line is drawn:

| Stroke | Means |
| --- | --- |
| **Solid** | Measured, calculated, or observed |
| **Dotted** | Projected, unverified, inferred, or absent from the record |

It applies to sparklines (measured history solid, projection dotted), to causal-chain
connectors (an `UNVERIFIED` link dots its connector), and to any trend mark. It costs
nothing, works in greyscale, and carries the same epistemic distinction the typography
carries — so `EvidenceClassTag` gains a graphical partner rather than standing alone.

**Hatch extends the same rule to fills.** Where a stroke would be dotted, a fill is
hatched at 45°: *this is not the thing itself*. It marks unassessed probability mass, a
prior-period reference bar, and any projected quantity. Adopted from reference review §14;
it turns two isolated devices into one system —

| Form | Measured / current | Not measured / not current |
| --- | --- | --- |
| Line | solid | dotted |
| Fill | solid | 45° hatch |

Two companions from the same source:

- **Annotate the delta, not the value.** A change is labelled on the mark itself
  (`Δ +1 from 0`), because Atlas is a delta product and the change is the subject.
- **Show the method quietly.** `probability_method`, a formula version, a scale — set small
  and muted at the edge of the block it governs. Provenance as texture rather than as a
  disclosure the owner must go looking for.

## 4. Certainty as weight

| Confidence | Treatment |
| --- | --- |
| High | Ink primary, normal weight |
| Moderate | Ink secondary |
| Low | Ink secondary + dotted underline on the claim |
| Unknown / unavailable | `—` in ink muted, with a reason on interaction |

`STALE`, `UNVERIFIED` and `CONFLICTING` add a small mono badge after the value, never a
colour wash. A stale number is still a number; it is not an error.

## 5. Space and density

Two densities, deliberately different:

- **Reading density** (Today, brief, Atlas view): 680 px measure, generous leading, wide
  section spacing. This is a document.
- **Scanning density** (State, Outlook, journal): compact rows, tabular alignment, tight
  leading. This is an instrument.

An 8 px spatial grid; 4 px only inside components. Sections separate with space and a
hairline rule with a small-caps label — never with a card.

## 6. Card philosophy

**Cards are used sparingly and mean something.** A card marks an object that can be opened,
acted on, or has its own identity — an impact, a scenario, a decision. Lists of attributes
are rows, not cards. Sections are space, not cards.

The failure mode being avoided is the SaaS card grid where everything is a rounded
rectangle and nothing has hierarchy. Border radius 6 px; hairline border; no shadow; no
hover lift — hover changes the border, not the elevation.

## 7. Iconography

Minimal and functional: direction arrows, disclosure chevrons, an external-link mark, a
lock for L3 data, a clock for staleness. Line icons, 1.5 px, matched to text size. **No
decorative icons, no illustrations, no empty-state art, no avatars, no AI sparkle
motifs.**

Attention classes are **words**, not icons. `ACTION` reads better than a triangle.

## 8. Motion

Motion shows causality and nothing else. Permitted: a value transitioning old → new when a
delta is revealed; disclosure expanding; a slide-over drawer. Duration 120–200 ms, standard
ease.

Prohibited: entrance animations, staggered list reveals, skeleton shimmer beyond 400 ms,
parallax, anything looping, anything celebratory. `prefers-reduced-motion` removes all of
it with no loss of meaning.

## 9. Light and dark

Both first-class; **dark is the default** — Atlas is most often read early and late, and
dark suits an instrument. Dark is a *selected* palette with its own steps validated against
the dark surface, never an inverted light theme. Both are declared explicitly; no theme
inherits its background from the host.

## 10. Data typography

- Currency: mono, tabular, grouped, currency code not symbol where ambiguous — `47,312 USD`.
- Percentages: mono, no decimals for probabilities (5-point steps), one decimal maximum
  for weights.
- Ordinal scores: mono, always signed, always with the scale — `+1` on `−3…+3`.
- Deltas: the change, then the origin — `+1 from 0`, never a bare arrow.
- Dates: `28 Aug 2026`; relative only under seven days.
- Durations and countdowns: `76 days` — never a progress ring.

## 11. Component surface summary

| Element | Treatment |
| --- | --- |
| Section header | Small caps, ink muted, hairline rule |
| Attention badge | Small caps word; accent only for `ACTION` |
| Evidence class tag | Lowercase mono, ink muted |
| Confidence | Word plus three-segment ordinal mark, never coloured |
| Sparkline | 2 px, ink secondary, no axes, no fill |
| Probability bar | Segmented, 2 px surface gaps, direct labels, hatched unassessed segment |
| Causal chain | Stepped list with hairline connectors — never a node graph |
| Drawer | Right slide-over, surface-raised, hairline left border |

## 12. Acceptance criteria

| # | Criterion |
| --- | --- |
| D1 | Every screen is fully comprehensible in greyscale |
| D2 | No meaning is carried by colour alone anywhere |
| D3 | Categorical palettes pass `validate_palette.js` in both modes before use |
| D4 | Interpretation, interface and measurement are typographically distinct on every screen |
| D5 | Colour appears at most three times per viewport in a normal state |
| D6 | Dark mode is separately validated, not an inversion |
| D7 | All motion is removable via `prefers-reduced-motion` with no loss of information |
| D8 | No shadow, glass, photographic ground or decorative illustration ships. The only gradient is the tonal page ground |
| D9 | Every line mark distinguishes measured (solid) from not-measured (dotted) |


---

## 13. Reference review — 2026-08

Four references scored against `VISUAL_REFERENCE_PROTOCOL.md`. Recorded because a design
system's value is in the choices it closed.

| Reference | Daily-use test | Verdict |
| --- | --- | --- |
| Property app — glass cards on a blurred architectural render, acid-green accent, memoji | **Fails.** A photographic ground delights on day 1 and obstructs on day 200; contrast over a photo is variable by definition | Rejected wholesale |
| Accounting app — frosted glass on a dusk landscape, radial gauges, large display numerals | **Fails** for the same reason. Radial gauges additionally imply a proportion of something, which most Atlas quantities are not | Rejected; **numeral confidence adopted** |
| Monitoring dashboard — near-black, glowing point-cloud map, status chips, dense small multiples | **Fails.** Designed for continuous anomaly-watching; Atlas is read for 30 seconds once a day. The density that makes it good makes Atlas bad | Rejected; the most seductive of the four, and the trap |
| Signal card — deep single-hue tonal field, one curve with dotted continuation, Δ annotation, formula at the edge | **Passes** | **Four mechanisms adopted** — §3b and the tonal ground |

### What the first three were actually communicating

Depth, numeral confidence, and evident craft. Those qualities are real and Atlas was
missing them. The mechanisms used to achieve them — glass, glow, photographic grounds,
neon — are not the only way to get them, and are the way that fails on day 200. The
adopted alternatives deliver the same three qualities using material rather than lighting.

### Questions resolved

| Question | Resolution |
| --- | --- |
| Q2 — how dark, and how much surface separation without shadow | Tonal ground plus hairline; raised surfaces separate by one step and a border, never by shadow |
| Q6 — how to show uncertainty graphically | The stroke rule (§3b): solid is measured, dotted is not |
| Q3 — how a dense screen stays calm | Not by borrowing monitoring-dashboard density. Row rhythm and a strict colour budget; revisit when State is built against real data |

Q1, Q4, Q5, Q7 and Q8 remain open. **Q8 — quiet rather than empty — was answered by none
of the four**, exactly as the protocol predicted: nobody publishes a quiet day.


---

## 14. Reference review — 2026-08, second set

Four further references, same studio, same signature: acid green or yellow on near-black,
glass, avatars, radial gauges, very large numerals. Consistent and well made. Scored
against the protocol; three mechanisms adopted.

### Adopted

**Hatch as the fill-side of the stroke rule.** One reference sets a prior-period bar as a
hatched block beside the current period as a solid one. That is the same epistemic
distinction Atlas already draws with solid-versus-dotted lines, extended to areas. Atlas
already hatched unassessed probability; this makes it a rule rather than a one-off (§3b).

**Numeral weight split.** `$23,` set heavy and `876` set lighter. It is not decoration —
it is a typographic expression of A12: emphasise magnitude, de-emphasise precision the
method does not really support. Applied to Atlas figures such as `14.2` months, where the
decimal carries less weight than the integer.

**Leader lines.** One reference draws a dotted line from an annotation to the exact point
on a chart it refers to. That is provenance made visual, and it is directly useful for
connecting an evidence chip to the point on a dimension's history where it landed. Dotted,
consistent with §3b.

### Refused

Acid green and yellow accents (neon, and one of them pairs green with red). Glass panels
and 3D renders. Avatars as a primary information device. Mesh and rainbow gradients.
Candlesticks.

**Radial gauges and speedometers, specifically.** They imply a proportion of a whole,
which most Atlas quantities are not — a `−3…+3` dimension score has no denominator. One
reference makes the failure vivid: its gauge sweeps from *Strong Sell* to *Strong Buy*.
That is a trading signal, which is the single output Atlas must never produce
(`PROGRAM.md` §2). The form carries the thing we rejected.

### Standing observation

Across all eight references, the qualities that attract are depth, numeral confidence and
evident craft. The mechanisms used to achieve them — lighting, neon, density — are the
ones that fail on day 200. Every adoption so far has substituted a material or structural
mechanism for a lighting one, and kept the quality.
