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
glass, no gradients**.

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
| D8 | No shadow, gradient, glass or decorative illustration ships |
