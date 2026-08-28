# Atlas Information Architecture

## 1. Evaluation of the proposed structure

The starting proposal was `Today · World · Me · Decisions · History · Ask Atlas`. Three of
those six do not survive scrutiny.

**`History` is not a place — it is a lens.** Every Atlas object has a past: world state at
a date, personal state at a date, the context frozen inside a decision. A separate History
tab forces the owner to *leave* the thing they are looking at in order to see its past,
and it duplicates every other screen in read-only form. Replaced by a global **as-of
cursor** that re-renders State and Outlook at any date. This is truer to A02, removes a
navigation item, and makes the time machine a *mode* rather than a screen to be built.

**`Ask Atlas` must not be a tab.** A conversational tab becomes the front door by habit,
and Atlas becomes a chatbot with a database attached — the explicit anti-goal. Replaced by
a global invocation (`⌘K`) available from every screen that **carries that screen's
context**. "Why?" on an impact *is* Ask Atlas, already scoped.

**`World` and `Me` are two halves of one question.** They answer "what does Atlas believe
right now", differ only in subject, and are always read together when interpreting an
impact. Merged into **State** with two views. This also frees a top-level slot for the
thing the original structure has no home for: standing impacts and scenarios, which
persist across days and cannot live only on Today.

## 2. Canonical top-level structure

Four sections, two global affordances. The four map one-to-one onto the core equation, so
the structure remains correct as Atlas grows.

| Section | Owner question | Core entities |
| --- | --- | --- |
| **Today** | What changed, and does it matter? | WorldStateDelta, Impact, ScenarioSet, Decision candidates |
| **State** | What does Atlas believe right now? | WorldStateSnapshot + Dimension; PersonalStateSnapshot, Account, Position, CashBalance, IncomeStream, GeographyState, Objective, Preference, Policy |
| **Outlook** | What am I exposed to, and what could happen? | Impact (standing), Scenario + ScenarioDriver, watches |
| **Decisions** | What did I decide, and how did it go? | Decision, Outcome, ForecastQuestion/Prediction/Resolution |

| Global affordance | Behaviour |
| --- | --- |
| **Ask** (`⌘K`) | Context-carrying query over structured state. Answers as cards with citations, never prose blobs. Available everywhere; owns no screen. |
| **As of** | Date cursor in the header. Sets the `as_of` for State and Outlook. Default "now". When set to a past date the entire chrome shifts to a historical treatment so the owner can never mistake past for present. |

### Why not five sections

`Today` could have been folded into `Outlook`. It is kept separate because the 30-second
read is the product's core habit and must not require a filter to reach. Conversely
`Outlook` cannot be folded into `Today`: an impact raised on Tuesday is still live on
Friday even though nothing changed, and Today shows only change.

## 3. Section specifications

### 3.1 Today

- **Purpose.** The delta lens. Everything material that changed since the last review,
  ranked, with personal meaning attached.
- **Question.** "Do I need to do anything, and if so what?"
- **Hierarchy.** Signal → what changed → what it means for you → Atlas view → what I would
  consider → scenarios (only if moved) → what would change this → what Atlas doesn't know
  → watching.
- **Primary objects.** The day's brief; `WorldStateDelta`; `Impact` (collapsed);
  decision candidates.
- **Must NOT show.** Unchanged dimensions. Standing impacts with no new evidence. Price
  moves producing no impact ≥ `REVIEW`. Repeated stories. Any section rendered as "no
  change" — omit it instead. More than three items above the fold.
- **Actions.** Mark each item `useful / noise / wrong`; open an impact; record a decision;
  acknowledge an `ACTION`; correct a value; ask.
- **Relationship to core.** Reads the `RunRecord` for the cycle and the brief built from
  it (Queue 13–14).

### 3.2 State

Two views under one section, switched by a segmented control, sharing the as-of cursor.

**State · World**
- **Question.** "What does Atlas believe about the world, and how sure is it?"
- **Hierarchy.** Regime summary → dimension list (default sorted by *personal relevance ×
  recent delta*, never alphabetically) → dimension detail → supporting narratives →
  evidence → sources.
- **Objects.** `WorldStateSnapshot`, `WorldStateDimension`, `WorldStateDelta`, `Narrative`,
  `Evidence`, `Source`.
- **Must NOT show.** A news list. Raw items as a feed. Dimensions the owner has no
  exposure to, above the fold. Any dimension without freshness and confidence.
- **Actions.** Inspect a dimension; open provenance; ask in context; pin a dimension.

**State · Me**
- **Question.** "What does Atlas believe about me, how fresh is it, and what is missing?"
- **Hierarchy.** Data health banner → capital → income → geography → objectives →
  preferences → policies.
- **Objects.** `PersonalStateSnapshot` and children, `Objective`, `Preference`, `Policy`.
- **Must NOT show.** A settings form. Editable fields that silently overwrite. Any value
  without source and `observed_at`. Atlas-proposed objectives mixed in with accepted ones.
- **Actions.** Correct a value (appends, never overwrites); accept/reject an
  Atlas-proposed objective; author an objective, preference or policy; view provenance.

### 3.3 Outlook

- **Question.** "What am I exposed to, and which futures is Atlas tracking?"
- **Hierarchy.** Attention summary → standing impacts ranked by priority → scenario sets
  by horizon → watches (named triggers with thresholds).
- **Objects.** `Impact`, `Scenario`, `ScenarioDriver`, watch definitions.
- **Must NOT show.** Aggregate risk scores. A single "Atlas score". Impacts of class
  `SUPPRESS` (available behind a filter, with the suppression reason).
- **Actions.** Filter by attention, domain, objective, direction; open impact detail;
  start a decision from an impact; inspect a scenario.
- **Note.** *Opportunities are not a separate area.* An opportunity is an `Impact` with a
  favourable direction and a non-empty `objective_refs`; it is filtered, not duplicated
  (cognitive-expansion review §A7).

### 3.4 Decisions

- **Question.** "What have I decided, on what basis, and was I right?"
- **Hierarchy.** Open decisions with review dates → decision journal → outcome
  retrospectives → calibration.
- **Objects.** `Decision`, `Outcome`, forecast ledger.
- **Must NOT show.** A trading journal. P&L as the measure of decision quality. Present-day
  values inside a historical decision without an explicit toggle.
- **Actions.** Record a decision; resolve an outcome; write a retrospective; add or update
  a forecast.

## 4. Navigation model

```
┌──────────────────────────────────────────────────────────────────┐
│  Atlas        Today   State   Outlook   Decisions      As of ▾  ⌘K│
└──────────────────────────────────────────────────────────────────┘
```

- Four items, flat. No nested navigation, no sidebar tree, no user-configurable layout.
- Detail lives in **routes**, not tabs: `/impact/:id`, `/decision/:id`,
  `/state/world/:dimension`.
- Depth is reached by **progressive disclosure inside a card**, not by adding navigation.
- Growth rule: a new capability extends an existing section or becomes a detail route. If
  a proposal seems to need a fifth top-level item, it is almost certainly a lens
  (like History) or a filter (like Opportunities) in disguise.

## 5. Anti-explosion guarantees

| Pressure | Resolution |
| --- | --- |
| Opportunities need visibility | Filter on Outlook, not a section |
| History / time machine | Global as-of cursor, not a section |
| Conversation | Global `⌘K`, not a section |
| Alerts (Queue 15) | Delivery channel; reuses the attention model, adds no vocabulary |
| Counterfactuals (later) | Route under Outlook: `/outlook/compare` |
| Calibration | Panel inside Decisions |
| Settings, privacy audit | One `/settings` route outside the four, never in the nav bar |
| "I want to see the news / the sources" | Reading Room under State, entered from Coverage or a claim — consequence-ordered, never a feed (`DOMAIN_SURFACES.md` §2) |
| "I want a geopolitics / economy section" | Category filter on State · World, not a top-level item |
| Documents, citizenship, movements | `/state/mobility` under State · Me |

## 6. Mapping to build queue

| Section | Becomes real at |
| --- | --- |
| Today | Queue 13 (cycle) → Queue 14 (brief) |
| Outlook · Impacts | Queue 09 |
| Outlook · Scenarios | Queue 10 |
| Decisions | Queue 12 |
| State · World | Queue 06 |
| State · Me | Queue 07–08 |
| As-of cursor | Queue 06+ for State; full time machine at Queue 16 |
| Ask | Queue 17 |
