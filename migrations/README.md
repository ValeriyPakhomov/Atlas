# Migrations

Alembic migrations against PostgreSQL 16 + pgvector. Revision `0caec4550b85` is the
**Queue 01** domain and persistence foundation.

Rules:

- Migrations must apply cleanly from an empty database (Queue 01 acceptance).
- Development and tests use Docker PostgreSQL 16; production uses Neon PostgreSQL 16 in
  AWS Frankfurt (`eu-central-1`). No SQLite compatibility path is supported.
- Use a direct PostgreSQL connection for Alembic and logical backup/restore workflows;
  application runtime may use a pooled connection.
- Neon is operational infrastructure, not a domain dependency. Migrations remain standard
  PostgreSQL/Alembic and off-provider logical backups are required.
- Material tables carry the temporal columns defined in `docs/DATA_MODEL.md`.
- State changes append rows and close the previous validity interval; migrations must
  not introduce destructive in-place updates of history (A02).
- Derived tables carry `run_id` and provenance columns (A05).
