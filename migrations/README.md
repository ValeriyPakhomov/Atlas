# Migrations

Alembic migrations against PostgreSQL 16 + pgvector. The first revision lands with
**Queue 01** (domain types and persistence foundation).

Rules:

- Migrations must apply cleanly from an empty database (Queue 01 acceptance).
- Material tables carry the temporal columns defined in `docs/DATA_MODEL.md`.
- State changes append rows and close the previous validity interval; migrations must
  not introduce destructive in-place updates of history (A02).
- Derived tables carry `run_id` and provenance columns (A05).
