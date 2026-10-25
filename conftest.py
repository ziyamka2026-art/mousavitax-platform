"""pytest configuration for MousaviTax AI Platform.

Run from repo root:  pytest -q tests
"""

import os
import sys
from pathlib import Path

# Add packages and apps to sys.path so tests can import them
ROOT = Path(__file__).resolve().parent.parent
for sub in ["packages", "apps/api", "services"]:
    p = ROOT / sub
    if p.exists():
        sys.path.insert(0, str(p))

# Disable Supabase/LLM access during tests — fail fast if tests try.
os.environ.setdefault("NODE_ENV", "test")
os.environ.setdefault("LLM_PROVIDER", "ollama")
os.environ.setdefault("API_SECRET_KEY", "test-secret-key-only-for-pytest")

# Markers
import pytest  # noqa: E402


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: fast, isolated unit tests")
    config.addinivalue_line("markers", "integration: tests touching external services")
    config.addinivalue_line("markers", "slow: long-running tests (>5s)")
    config.addinivalue_line("markers", "rag: RAG pipeline tests")
    config.addinivalue_line("markers", "rbac: authorization tests")


def pytest_addoption(parser):
    """Register custom CLI options."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests (skipped by default)",
    )


def pytest_collection_modifyitems(config, items):
    """Auto-skip integration tests unless --run-integration is passed."""
    if not config.getoption("--run-integration"):
        skip = pytest.mark.skip(reason="needs --run-integration")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip)
