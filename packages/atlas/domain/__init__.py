"""Atlas domain — dependency-light types and rules (Queue 01+).

Constitutional constraint (ADR-0001, ADR-0004): this package must remain importable
with no network access and must not import web frameworks, ORMs, HTTP clients, LLM
SDKs, agent frameworks, or data-provider SDKs. ``tests/unit/test_architecture_boundaries.py``
enforces this mechanically.
"""
