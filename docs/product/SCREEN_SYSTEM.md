# Atlas Screen System

Every screen carries a priority: `V0` (ships with the Daily Brief, Queue 14), `V1`
(Queue 16), `LATER` (post-V1). Anything not listed is not planned.

---

## 1. Route map

```
V0     /                       Today
V0     /brief/:date            Brief archive
V0     /impact/:id             Impact detail
V0     /decisions              Decision journal
V0     /decision/:id           Decision detail
V0     /settings/data          Data health and corrections

V1     /state                  State · Me (default)
V1     /state/world            State · World
V1     /state/world/:key       Dimension detail
V1     /outlook                Outlook
V1     /scenario/:id           Scenario detail
V1     /objectives             Objectives and preferences
V1     /decisions/calibration  Calibration
V1     /settings/privacy       Privacy and transmission audit
V1     /state/sources          Reading Room — what Atlas read, and what it discarded
V1     /state/mobility         Mobility & Documents — permits, allowances, bases

LATER  /outlook/compare        Counterfactual comparison
LATER  /state/geography/:code  Geography detail
```

Six V0 routes. Detail lives in routes; depth lives in progressive disclosure inside cards.

---

## 2. Screen specifications

### `/` — Today · **V0**

| | |
| --- | --- |
| **Purpose** | The delta lens; the 30-second answer |
| **Entry** | Default route, notification, bookmark |
| **Primary information** | Signal, what changed, ranked impacts, Atlas view |
| **Primary action** | Mark items `useful/noise/wrong` |
| **Secondary** | Open impact, record decision, acknowledge `ACTION`, correct a value, ask |
| **Empty state** | The quiet day (`TODAY_AND_DAILY_BRIEF.md` §7) — never a blank slate |
| **Error state** | Cycle failed: state the failure, the last successful cycle time, and what is therefore unknown. Never render a stale brief as current |
| **Mobile** | Full parity. This screen is designed mobile-first |
| **Later** | Triage band, richer watch countdowns |

### `/brief/:date` — Brief archive · **V0**

Identical rendering to Today with a historical chrome treatment and prev/next navigation.
Values are frozen as published; nothing recomputes. Empty state: "No cycle ran on this
date" with the nearest dates that did.

### `/impact/:id` — Impact detail · **V0**

| | |
| --- | --- |
| **Purpose** | Understand one impact completely, then act |
| **Entry** | Today, Outlook, decision, Ask citation |
| **Primary information** | Claim, components, causal chain, invalidators, objectives |
| **Primary action** | Record a decision from this impact |
| **Secondary** | Open forensic view, correct an input, ask in context, change attention |
| **Empty state** | n/a |
| **Error state** | `SUPPRESS`ed impact opens with its suppression reason shown, not hidden |
| **Mobile** | Collapsed and expanded tiers; forensic view is desktop-first but reachable |

### `/decisions`, `/decision/:id` — **V0**

Journal grouped by review status: *due for review · open · resolved*. Cross-domain by
construction — filters are `domain` and `objective`, never asset class.

Decision detail renders the **frozen context**: impacts, scenarios, objectives active, and
policy results as they were at `decision_time`. Present-day values are hidden behind an
explicit `show what we know now` toggle (see `COMPONENT_SYSTEM.md` §12).

Empty state: "No decisions recorded yet. Atlas records what you knew at the time, which is
what makes a retrospective honest."

### `/settings/data` — Data health and corrections · **V0**

The one settings surface that ships in V0, because A06 requires the owner to be able to
see and fix what Atlas has wrong. Lists every personal-state value with source,
`observed_at`, freshness status and a correct action. Sorted by staleness.

### `/state`, `/state/world`, `/state/world/:key` — **V1**

Me and World per `INFORMATION_ARCHITECTURE.md` §3.2. Dimension detail shows score history
as a sparkline of the ordinal score, current confidence and freshness, supporting and
contradicting narratives, evidence, and the impacts that reference it.

### `/outlook` — **V1**

Standing impacts and scenario sets. Filters: attention, domain, objective, direction. The
*opportunity view* is the direction filter plus a non-empty objective link — not a
separate screen.

### `/scenario/:id` — **V1**

Thesis, probability with unassessed mass, drivers with direction and weight, invalidators,
movement history, personal implications as links to impacts.

### `/objectives` — **V1**

Active objectives, preference ordering, and a distinct **Atlas noticed** tray for proposed
objectives awaiting acceptance (`COMPONENT_SYSTEM.md` §9).

### `/decisions/calibration` — **V1**

Resolved forecasts, owner versus Atlas, by domain. Restrained: a table and a small
reliability plot, no leaderboard, no streaks, no scores presented as achievement.

### `/settings/privacy` — **V1**

Data tiers in use, which providers hold which clearance, and the transmission log —
what left the perimeter, when, at what tier.

### `/state/sources` — Reading Room · **V1**

The evidence ledger, not a news feed: material items first with what each produced,
discarded items with the reason, and unresolved conflicts. Entry is from the brief's
`Coverage` line or from any claim — never from the navigation bar. Full specification in
`DOMAIN_SURFACES.md` §2.

### `/state/mobility` — Mobility & Documents · **V1**

Documents with what each one gates, day-counters (Schengen 90/180, tax residence), and the
base roles. Deadlines are countdowns in days, never progress rings. L3 throughout, so the
surface carries the local-only indicator. Full specification in `DOMAIN_SURFACES.md` §4.

### `/outlook/compare` — **LATER**

Counterfactual option comparison (`COMPONENT_SYSTEM.md` §14). No aggregate scores.

---

## 3. Cross-cutting states

Every screen implements all six. They are designed states with fixed copy patterns, not
error toasts.

| State | Meaning | Treatment |
| --- | --- | --- |
| `UNKNOWN` | Never established | Value slot shows `—` with a reason on hover/tap. Never blank, never zero |
| `STALE` | Beyond freshness SLA | Value shown with age badge: `9d stale`. Any conclusion using it is marked derived-from-stale |
| `MISSING` | Expected but absent | Named explicitly with what it blocks |
| `CONFLICTING` | Sources disagree | Both values shown with sources. Atlas does not pick silently |
| `UNVERIFIED` | Asserted, not confirmed | Badge plus the verification that would settle it |
| `DEGRADED` | Output produced with reduced integrity | Banner at the top of the affected section naming the reason |

Prohibited: a spinner that resolves to plausible text; a zero standing in for unknown; a
chart drawn through missing points.

---

## 4. Responsive split

| Belongs on mobile | Belongs on desktop |
| --- | --- |
| Today, in full | Dimension drill-down |
| Brief archive | Forensic provenance view |
| Impact collapsed + expanded | Counterfactual comparison |
| Decision capture and review | Calibration analytics |
| Correcting a value | Time-machine diffing |
| Acknowledging an `ACTION` | Objective and preference authoring |
| Feedback marking | Multi-scenario comparison |

Mobile is not a compressed desktop dashboard. It carries the **daily habit** — read,
judge, decide, correct. Desktop carries **investigation**. A capability that exists only
on desktop must never be required to complete a daily loop.

---

## 5. What is deliberately absent

No news feed. No chat homepage. No widget marketplace or configurable layout. No KPI wall.
No trading terminal or order ticket. No task manager, email client or calendar. No social,
sharing, streaks or achievements. No onboarding wizard — Atlas has one user, configured
once through `/settings/data`. No notification centre — alerts are delivered, and their
state lives in Outlook.
