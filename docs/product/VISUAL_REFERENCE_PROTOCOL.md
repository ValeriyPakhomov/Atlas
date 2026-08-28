# Visual Reference Protocol

How references are used on Atlas, and how they are prevented from diluting it.

---

## 1. The failure this exists to prevent

Collecting twenty references and extracting "the maximum list of parameters" produces a
**mood board**, and mood boards average aesthetics into something with no position. Worse,
references are selected for how impressive they look in a portfolio — which selects for
exactly the properties Atlas has already rejected: hero gradients, glass, dense
dashboards, neon accents, decorative motion.

Atlas's visual direction is already **decided and measured**: the palette is validated
against CVD and contrast, the typographic role system encodes epistemics, and the
anti-patterns are enumerated. A reference pass that starts from "what do we like" will
quietly relitigate all of it.

## 2. The inversion

> **Do not extract parameters from references. Extract answers to questions.**

Write the open visual questions **before** looking at anything. Then references become
evidence, and each one is scored on whether it answers a question we actually have.

This is the same discipline as recording a forecast before the outcome is known — which is
appropriate, since it is the discipline the product itself is built on.

## 3. Atlas's open visual questions

Written before the reference session. These are the only things a reference can decide.

| # | Question | Why it cannot be answered on paper |
| --- | --- | --- |
| Q1 | How much contrast between serif and sans before the page reads as two products rather than two voices? | A ratio judgement that only shows up rendered |
| Q2 | How dark is "dark but not black", and how much separation do raised surfaces need without shadow? | Depends on real content density |
| Q3 | How do you make a dense, tabular screen feel calm rather than administrative? | The hardest problem in State and Outlook |
| Q4 | What does a hairline-only elevation system look like at 1×, and does it survive on a laptop screen? | Hairlines are where restraint most often fails |
| Q5 | How do you show a countdown or a deadline with weight but without alarm? | The residency surface lives or dies on this |
| Q6 | How is uncertainty shown typographically — weight, opacity, or something else? | Almost nothing does this; the ones that do are worth studying |
| Q7 | How much space can a page give a single sentence before it reads as pretentious? | The Signal line is the product's first impression |
| Q8 | What makes an interface feel *quiet* rather than *empty*? | The single highest-stakes question in Atlas |

**Q8 is the one that matters most.** The quiet day is the most common screen, and no
reference in a portfolio will ever be a quiet day — so it is the question most likely to go
unanswered unless it is asked deliberately.

## 4. Extraction schema

One row per reference, same fields every time, so twenty references produce comparable data
rather than twenty essays.

| Field | Captured |
| --- | --- |
| **Identity** | What it is; medium (marketing page / product UI / print / OS); density class |
| **Daily-use test** | Would this still feel good on day 200, opened for 30 seconds every morning? |
| **Type** | Families; role split; scale ratio; measure; numerals tabular or not; weight range actually used |
| **Surface & light** | Background values; elevation strategy (shadow / border / none); flat or lit; single or dual theme |
| **Colour** | Hue count in one viewport; what colour is *for* (semantic / brand / decoration); accent frequency |
| **Texture** | none / noise / paper / hatch / dither — and where applied |
| **Structure** | Grid; spacing rhythm; card usage; separator strategy |
| **Data** | How numbers are set; whether uncertainty is expressed at all; chart restraint |
| **Motion** | Present, purposeful, or decorative |
| **One mechanism worth taking** | A single sentence — the specific technique, not the vibe |
| **Answers which question** | Q1–Q8, or *none* |
| **Transferability** | high / medium / none, with the reason |

A reference that answers no question and offers no mechanism scores zero. **That is a valid
and common result**, and recording it is what keeps the exercise honest.

## 5. The transferability filter

Most reference properties do not survive the trip to a daily-use instrument.

| Transfers well | Transfers badly |
| --- | --- |
| Typographic hierarchy and scale | Hero treatments — Atlas has no hero |
| Spacing rhythm and measure | Scroll-driven choreography |
| Separator and elevation strategy | Marketing-page lighting and gradients |
| Numeral and table treatment | Density borrowed from trading terminals |
| Restraint in colour frequency | Brand-expressive accents |
| Empty and quiet state handling | Illustration and mascot systems |

**The rule:** a marketing page is designed to be seen once and impress. Atlas is designed to
be opened a thousand times and *not* impress. Anything optimised for the first impression is
suspect by default.

## 6. Hard constraints — not negotiable by any reference

These come from `PRODUCT_PRINCIPLES.md` and `DESIGN_DIRECTION.md` and are not open for
reference-driven revision:

- No meaning carried by colour alone; every screen readable in greyscale.
- Uncertainty is weight and opacity, never colour.
- Categorical palettes pass `validate_palette.js` in both modes before use.
- Three typographic roles remain distinct: interpretation, interface, measurement.
- No shadow, gradient, glass or decorative illustration.
- Colour appears at most three times per viewport in a normal state.
- Motion only shows causality; all of it removable via `prefers-reduced-motion`.

A reference that is beautiful *because* it violates one of these is evidence about that
reference's product, not about Atlas.

## 7. Procedure

1. **Baseline first.** Look at the live Atlas prototype before the references, and note
   what is wrong with it. Judging references without a baseline produces preference; judging
   them against a baseline produces decisions.
2. **Score all references** against the schema in §4 — fast, one pass, no deliberation.
3. **Group by question.** Which references speak to Q1, to Q3, to Q8.
4. **Decide each question once**, citing the specific reference and mechanism.
5. **Record what was rejected and why** — this is the durable artefact. A design system's
   value is in the choices it closed, not the ones it left open.
6. **Update `DESIGN_DIRECTION.md`** with the resolved questions. Anything unresolved stays
   an open question rather than becoming an untested preference.

## 8. Third-party design systems

Where an existing library or kit is proposed as a source:

- Take **mechanisms** — spacing scales, state patterns, component anatomies.
- Do not take **identity** — palettes, brand type, iconography — since Atlas's identity is
  derived from its own constraints (validated colour, epistemic type) rather than chosen.
- Licence applies to design assets as it does to code: check before adopting, and record
  the source in `THIRD_PARTY_NOTICES.md` if anything is actually reused (ADR-0005).
