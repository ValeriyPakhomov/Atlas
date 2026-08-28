# Security and Privacy

Atlas holds a complete financial, geographic and residency picture of one person. The
threat model is not abuse of Atlas by its owner; it is **compromise of the store**, and
**quiet scope creep** from read-only analysis toward account access.

## Absolute prohibitions

Atlas must never store, log, cache, embed or transmit:

- crypto seed phrases or mnemonics;
- private keys of any kind;
- exchange withdrawal secrets or API keys with withdrawal rights;
- banking passwords;
- raw authentication cookies where avoidable.

There is no configuration, adapter or emergency path that makes any of these
acceptable. A feature that requires one is out of scope by definition.

## Repository visibility

**This repository is public.** Everything committed is permanently readable, and git
history cannot be retracted once pushed — a later force-push does not remove content
from forks, clones or caches.

Therefore the prohibitions above are not merely runtime rules; they are **commit-time**
rules. Never commit:

- personal state of any kind: balances, positions, account or wallet identifiers,
  residency documents, addresses, deadlines tied to a real person;
- fixtures derived from real personal data — golden and eval fixtures are synthetic;
- configuration values. `.env.example` carries names and comments only.

Before any queue item that touches personal state (Queue 07 onward), confirm that the
data path terminates in the database, never in the repository. If a capability genuinely
requires committed personal content, it belongs in a private deployment or a private
repository, decided **before** the code is written.

CI runs secret scanning, but scanning is a backstop, not the control. The control is
that personal data never enters a commit in the first place.

## Credential rules

- Read-only API credentials only, with trading and withdrawal **disabled at the
  provider**. A credential that *can* withdraw is a violation even if unused (ADR-0003).
- Separate secrets per environment. No production secret ever reaches a developer machine.
- Secrets live in a provider secret manager. `.env` is for local development and is
  git-ignored; `.env.example` carries names and comments only, never values.
- Least privilege everywhere, including the database role used by each service.

## Data handling

- Transport encrypted; database encryption at rest via the provider.
- Backups **and a tested restore**. An untested backup is not a backup.
- No PII, real balances or production data in fixtures, tests, logs or telemetry. Golden
  fixtures use synthetic personal state.
- Every personal-state mutation is audit-logged: who or what proposed it, which adapter
  or human confirmed it, the previous and new values, and the run.
- Model prompts and traces are treated as sensitive: they contain personal state by
  construction.

## Untrusted input

Ingested content is **data, never instruction**. Source text, article bodies, feed
items and page content must not be able to steer Atlas's behaviour. Extraction runs
with structured output schemas; a model proposal is validated for schema, bounds,
provenance and permission before storage (A04). Prompt-injection attempts in a source
item should surface as low verification status, not as a state change.

## Service controls

- No public admin endpoints. API docs are exposed only in `local` and `ci`.
- Rate limiting on the API surface.
- CSRF and session protections for the dashboard.
- Dependency scanning and secret scanning in CI.
- MCP tools are read-only in V1, except explicitly scoped, human-confirmed owner
  updates (Queue 17).

## Future execution

If external execution is ever added, it is a **separate subsystem with its own security
boundary**: separate credentials, separate deployment, per-action human approval,
idempotency keys and a dedicated audit trail. It is not a flag in this codebase, and it
requires an ADR superseding ADR-0003.
