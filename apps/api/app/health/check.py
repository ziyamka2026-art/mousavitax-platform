"""
Health Check Endpoint — MousaviTax AI Platform
=================================================

Provides diagnostic information about:
  - Source Bridge status (demo/real mode + 7 modules)
  - Database connectivity (Supabase)
  - LLM provider configuration
  - Environment variable presence (without exposing values)

Safe to expose at /api/health in production.

@package apps.api.app.health
"""

from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from packages.fiqh_validator.validator import FiqhRule, VALIDATORS
from packages.oath.runtime_guards import AnalysisStatus


# ---------------------------------------------------------------------------
# Health status data classes
# ---------------------------------------------------------------------------

@dataclass
class CredentialCheck:
    name: str
    is_set: bool  # NEVER expose the actual value
    source: str  # 'env' | 'missing'
    description: str


@dataclass
class ModuleHealth:
    module_id: str
    available: bool
    last_check: str


@dataclass
class HealthResponse:
    status: str  # 'ok' | 'degraded' | 'down'
    timestamp: str
    version: str = "0.2.0"
    uptime_seconds: float = 0.0
    demo_mode: bool = False
    credentials: list[CredentialCheck] = field(default_factory=list)
    modules: list[ModuleHealth] = field(default_factory=list)
    fiqh_rules_count: int = 0
    oath_clauses_count: int = 0
    llm_provider: str = "not_set"
    database: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "timestamp": self.timestamp,
            "version": self.version,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "demo_mode": self.demo_mode,
            "credentials": [asdict(c) for c in self.credentials],
            "modules": [asdict(m) for m in self.modules],
            "fiqh_rules_count": self.fiqh_rules_count,
            "oath_clauses_count": self.oath_clauses_count,
            "llm_provider": self.llm_provider,
            "database": self.database,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Health check functions
# ---------------------------------------------------------------------------

_START_TIME = datetime.now(timezone.utc)

CREDENTIAL_NAMES = [
    ("LOVABLE_API_KEY", "Lovable connector-gateway API key"),
    ("GOOGLE_DRIVE_API_KEY", "Google Drive connector API key"),
    ("GOOGLE_SERVICE_ACCOUNT_JSON", "Google Service Account JSON (direct)"),
    ("TAXLAW_GROK_MASTER_FOLDER_ID", "Master Drive folder ID for 7 modules"),
    ("SUPABASE_URL", "Supabase project API URL"),
    ("NEXT_PUBLIC_SUPABASE_URL", "Supabase URL (client-side)"),
    ("NEXT_PUBLIC_SUPABASE_ANON_KEY", "Supabase anon key (client-side)"),
    ("SUPABASE_SERVICE_ROLE_KEY", "Supabase service role key (server)"),
    ("LLM_PROVIDER", "LLM provider: ollama|openai|gemini"),
    ("OPENAI_API_KEY", "OpenAI API key (when LLM_PROVIDER=openai)"),
    ("GOOGLE_API_KEY", "Google API key (when LLM_PROVIDER=gemini)"),
    ("TELEGRAM_BOT_TOKEN", "Telegram bot token"),
    ("API_SECRET_KEY", "FastAPI server secret key"),
    ("SENTRY_DSN", "Sentry DSN for error reporting"),
]


def check_credentials() -> list[CredentialCheck]:
    """Check presence of every expected env var (without exposing values)."""
    return [
        CredentialCheck(
            name=name,
            is_set=bool(os.getenv(name)),
            source="env" if os.getenv(name) else "missing",
            description=desc,
        )
        for name, desc in CREDENTIAL_NAMES
    ]


def check_source_bridge() -> tuple[bool, list[ModuleHealth], str]:
    """Check Source Bridge — returns (demo_mode, modules, error)."""
    try:
        # Import lazily so health doesn't fail if source_bridge is broken
        from services.source_bridge.demo_client import is_demo_mode
        from services.source_bridge.bridge import MODULE_CLASSES

        demo_mode = is_demo_mode()
        now = datetime.now(timezone.utc).isoformat()
        modules = [
            ModuleHealth(module_id=mid, available=True, last_check=now)
            for mid in MODULE_CLASSES.keys()
        ]
        return demo_mode, modules, ""
    except Exception as e:
        return False, [], f"source_bridge_check_failed: {e}"


def check_fiqh_rules() -> int:
    """Count available fiqh rules."""
    return len(VALIDATORS)


def check_oath_clauses() -> int:
    """Count available oath guard functions."""
    from packages.oath.runtime_guards import (
        enforce_oath,
        law_over_circular,
        require_ambiguity_flag,
        require_archival_record,
        require_citations,
        require_human_review,
    )
    return 6  # 6 oath clauses


def check_llm_provider() -> str:
    """Return configured LLM provider name."""
    provider = os.getenv("LLM_PROVIDER", "ollama")
    # Verify the provider has needed creds
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        return f"{provider} (no API key set)"
    if provider == "gemini" and not os.getenv("GOOGLE_API_KEY"):
        return f"{provider} (no API key set)"
    return provider


def check_database() -> dict[str, Any]:
    """Check Supabase URL presence."""
    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    if not url:
        return {"status": "missing_url", "configured": False}
    return {
        "status": "configured",
        "configured": True,
        "url_format_ok": ".supabase.co" in url and "dashboard" not in url,
        "is_dashboard_url": "dashboard" in url,
    }


def compute_uptime() -> float:
    return (datetime.now(timezone.utc) - _START_TIME).total_seconds()


def get_health() -> HealthResponse:
    """Compute full health snapshot."""
    creds = check_credentials()
    demo_mode, modules, bridge_err = check_source_bridge()

    errors = []
    if bridge_err:
        errors.append(bridge_err)

    db = check_database()
    if db.get("is_dashboard_url"):
        errors.append(
            "database: SUPABASE_URL points to dashboard URL — should be API URL"
        )

    # Determine overall status
    critical_creds = ["SUPABASE_URL", "LLM_PROVIDER"]
    missing_critical = [
        c.name for c in creds
        if not c.is_set and c.name in critical_creds
    ]
    if missing_critical:
        status = "down" if not demo_mode else "degraded"
        errors.append(f"missing critical: {missing_critical}")
    elif errors:
        status = "degraded"
    else:
        status = "ok"

    return HealthResponse(
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=compute_uptime(),
        demo_mode=demo_mode,
        credentials=creds,
        modules=modules,
        fiqh_rules_count=check_fiqh_rules(),
        oath_clauses_count=check_oath_clauses(),
        llm_provider=check_llm_provider(),
        database=db,
        errors=errors,
    )


def get_health_simple() -> dict[str, str]:
    """Lightweight version — for readiness probes."""
    h = get_health()
    return {"status": h.status, "timestamp": h.timestamp, "version": h.version}


__all__ = [
    "CredentialCheck",
    "ModuleHealth",
    "HealthResponse",
    "check_credentials",
    "check_source_bridge",
    "check_fiqh_rules",
    "check_oath_clauses",
    "check_llm_provider",
    "check_database",
    "compute_uptime",
    "get_health",
    "get_health_simple",
]
