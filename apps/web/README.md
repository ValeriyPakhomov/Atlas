# Atlas dashboard (Queue 16)

Next.js + React + TypeScript. Not yet implemented — this directory fixes ownership so
the JS toolchain arrives with the dashboard rather than as an empty lockfile
(`docs/ARCHITECTURE.md` §10, deviations).

Information architecture (blueprint §22):

| Screen | Purpose |
| --- | --- |
| Home / Today | **What changed** — a state delta, never a database dump |
| World | Dimensions, narratives, evidence, change history |
| Personal | Assets, cash, currencies, income, runway, geography, deadlines, goals, policies |
| Impact | Cross-domain causal chains ranked by priority |
| Scenarios | Probability history and driver changes |
| Life Fortress | Country/city matrix with scores, evidence, trend, owner fit |
| Decisions | Journal, outcomes, calibration, "what Atlas got wrong" |
| Sources | Freshness, reliability, failures, provenance |

Constraint: the dashboard reads the backend. **No business logic in the frontend**
(Queue 16 acceptance).
