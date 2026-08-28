# Atlas Product Principles

Twenty durable rules. They exist to prevent drift: when a future screen, feature or
"quick improvement" is proposed, it is checked against these before it is designed.

A principle here is not a preference. Violating one is a product defect.

---

**1. Atlas answers five questions, and only five.**
What changed? Why does it matter to me? What should I consider doing? How sure are we?
What would change this conclusion? A screen that answers none of them does not belong.

**2. The owner does not operate Atlas.**
Atlas runs whether or not anyone opens it. The interface is a window onto work already
done, never a control panel that must be driven.

**3. Saying nothing is a feature.**
"Nothing material changed" is a successful, complete output. A quiet day must look
deliberate and trustworthy, never empty or broken. Any pressure to fill the page is the
beginning of the end of the product.

**4. Show deltas, not inventory — and never a feed.**
Today shows what changed. Standing state lives in State and Outlook. Restating a stable
fact is noise, however true it is. Nothing in Atlas is ordered by recency: sources are
shown ordered by what they produced, with discards and their reasons, which builds trust
that browsing headlines destroys.

**5. Never blend the five kinds of change.**
World, You, Impact, Scenario and Decision changes are structurally different and are never
rendered as one undifferentiated feed.

**6. Fact, inference and speculation are never styled alike.**
Every claim carries its evidence class (`DIRECT_CALCULATED`, `DIRECT_RULE`,
`INFERRED_CAUSAL`, `SPECULATIVE`). A calculated mark-to-market and a geopolitical hunch
must be visually impossible to confuse.

**7. Type encodes epistemics.**
Serif is Atlas interpreting. Sans is the interface speaking. Mono is a measured value.
The owner learns to read the difference without being told.

**8. Uncertainty is never a colour.**
Confidence is carried by weight, opacity and explicit bands. Colour is reserved for
direction and for the single interrupting attention class.

**9. No fake precision, anywhere.**
Probabilities display in 5-point steps; a change is shown only when it crosses a step.
Confidence displays as a band. The stored value keeps full precision; the screen does not.

**10. Unassessed is not zero.**
Missing probability mass is shown as its own segment labelled *not assessed*. It is never
redistributed to make a set look complete.

**11. Fail loud, in the interface too.**
`UNKNOWN`, `STALE`, `MISSING`, `CONFLICTING`, `UNVERIFIED`, `DEGRADED` are designed
states with designed copy. Atlas never replaces missing truth with plausible text.

**12. Every conclusion is traceable in three clicks.**
Claim → causal chain → evidence → source. Provenance is always reachable and never
mandatory to read.

**13. Every conclusion states what would falsify it.**
A recommendation without an invalidator is an opinion. Invalidators are a required field,
not a nice-to-have.

**14. Interrupt only when the value of interrupting exceeds its cost.**
`ACTION` is the sole interrupting class and requires a qualifying deterministic rule or
strong multi-source evidence. Every false interruption costs more trust than ten correct
ones earn.

**15. The owner authors values; Atlas may only propose them.**
Atlas-proposed objectives and preferences are visually distinct and inert until accepted.
Atlas never infers what the owner wants and then optimises against it.

**16. Canonical truth is corrected, never overwritten.**
A correction appends a new observation with owner authorship. The prior value stays
visible. No LLM writes canonical state.

**17. Show the past as it was known then.**
Historical decisions render their frozen context. Present-day values are hidden behind an
explicit toggle, because hindsight contamination destroys the ability to learn.

**18. Outcome quality is not decision quality.**
A good decision with a bad outcome is a distinct, first-class result. The retrospective
never collapses the two.

**19. No aggregate scores across incommensurable dimensions.**
No "87/100" for a city, an option or a portfolio. Weighting money against optionality
against career requires trade-off rates the owner cannot reliably state (ADR-0011).
Compare dimension by dimension and let the owner weigh.

**20. Conversation is a lens, never the home.**
Ask Atlas queries structured state from wherever the owner already is, and answers in
cards with citations. The moment a chat box becomes the front door, Atlas has become a
chatbot with a database attached.
