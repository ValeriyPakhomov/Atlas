"""Mechanical enforcement of the Atlas dependency rule.

Blueprint §5 and ADR-0001: ``packages/atlas/domain`` must stay framework-neutral and
testable with no network access. A rule that lives only in a document decays; this
test makes it fail CI instead.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.conftest import DOMAIN_ROOT, PACKAGES_ROOT, REPO_ROOT

FORBIDDEN_IN_DOMAIN = {
    # web / service frameworks
    "fastapi",
    "starlette",
    "uvicorn",
    "flask",
    "django",
    # persistence and transport
    "sqlalchemy",
    "sqlmodel",
    "alembic",
    "psycopg",
    "psycopg2",
    "asyncpg",
    "redis",
    "httpx",
    "requests",
    "aiohttp",
    "urllib3",
    "urllib",
    "socket",
    # validation / settings frameworks (domain uses stdlib dataclasses)
    "pydantic",
    "pydantic_settings",
    # LLM and agent frameworks
    "openai",
    "anthropic",
    "langchain",
    "langchain_core",
    "langgraph",
    "litellm",
    "instructor",
    # third-party data and memory platforms
    "openbb",
    "mem0",
    "qlib",
    # Atlas infrastructure
    "atlas.config",
}


def _module_roots(tree: ast.AST) -> set[str]:
    """Top-level module names imported by a parsed source file."""
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name)
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import, stays inside the package
                continue
            if node.module:
                roots.add(node.module)
                roots.add(node.module.split(".", 1)[0])
    return roots


def _python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


@pytest.mark.parametrize("path", _python_files(DOMAIN_ROOT), ids=lambda p: p.name)
def test_domain_has_no_framework_or_network_imports(path: Path) -> None:
    imported = _module_roots(ast.parse(path.read_text(encoding="utf-8")))
    violations = sorted(imported & FORBIDDEN_IN_DOMAIN)
    assert not violations, (
        f"{path.relative_to(REPO_ROOT)} imports {violations}; "
        "the domain package must stay framework-neutral and offline-testable (ADR-0001)"
    )


@pytest.mark.parametrize("path", _python_files(PACKAGES_ROOT), ids=lambda p: p.name)
def test_library_packages_do_not_import_deployable_apps(path: Path) -> None:
    imported = _module_roots(ast.parse(path.read_text(encoding="utf-8")))
    violations = sorted(m for m in imported if m in {"atlas_api", "atlas_worker"})
    assert not violations, (
        f"{path.relative_to(REPO_ROOT)} imports {violations}; "
        "dependencies point from apps/ into packages/, never the reverse"
    )


def test_domain_is_importable_without_optional_dependencies() -> None:
    """Domain must import with nothing but the standard library available."""
    import atlas.domain.clock as clock_module

    assert clock_module.__name__ == "atlas.domain.clock"
