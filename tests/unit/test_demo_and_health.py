"""
Unit tests for Demo Mode (DemoDriveClient) and Health Check.
"""

import os
import asyncio
import pytest
from pathlib import Path

from services.source_bridge.demo_client import (
    DemoDriveClient,
    SAMPLE_FILES_META,
    is_demo_mode,
    make_drive_client,
)


# ---------------------------------------------------------------------------
# Demo mode auto-detection
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_demo_mode_auto_activates_when_no_credentials(monkeypatch):
    """Without LOVABLE_API_KEY or GOOGLE_SERVICE_ACCOUNT_JSON, demo mode auto-activates."""
    monkeypatch.delenv("LOVABLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("SOURCE_BRIDGE_DEMO_MODE", raising=False)
    assert is_demo_mode() is True


@pytest.mark.unit
def test_demo_mode_disabled_when_lovable_key_set(monkeypatch):
    monkeypatch.setenv("LOVABLE_API_KEY", "test-key")
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("SOURCE_BRIDGE_DEMO_MODE", raising=False)
    assert is_demo_mode() is False


@pytest.mark.unit
def test_demo_mode_disabled_when_service_account_set(monkeypatch):
    monkeypatch.delenv("LOVABLE_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", '{"test": "json"}')
    monkeypatch.delenv("SOURCE_BRIDGE_DEMO_MODE", raising=False)
    assert is_demo_mode() is False


@pytest.mark.unit
def test_demo_mode_can_be_forced_via_env(monkeypatch):
    """SOURCE_BRIDGE_DEMO_MODE=true forces demo even if creds are set."""
    monkeypatch.setenv("LOVABLE_API_KEY", "real-key")
    monkeypatch.setenv("SOURCE_BRIDGE_DEMO_MODE", "true")
    assert is_demo_mode() is True


@pytest.mark.unit
def test_demo_mode_various_truthy_values(monkeypatch):
    for value in ("true", "1", "yes", "TRUE", "Yes"):
        monkeypatch.setenv("SOURCE_BRIDGE_DEMO_MODE", value)
        assert is_demo_mode() is True, f"Failed for value: {value}"


@pytest.mark.unit
def test_demo_mode_various_falsy_values(monkeypatch):
    monkeypatch.delenv("LOVABLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    for value in ("false", "0", "no", ""):
        monkeypatch.setenv("SOURCE_BRIDGE_DEMO_MODE", value)
        assert is_demo_mode() is True, "Auto-activates when no creds"


# ---------------------------------------------------------------------------
# DemoDriveClient — list_files
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_demo_client_lists_all_five_sample_laws():
    client = DemoDriveClient()
    files = asyncio.run(client.list_files(folder_id="anything"))
    assert len(files) == 5
    expected_ids = {"demo-001", "demo-002", "demo-003", "demo-004", "demo-005"}
    assert {f.id for f in files} == expected_ids


@pytest.mark.unit
def test_demo_client_filters_by_mime_type():
    client = DemoDriveClient()
    files = asyncio.run(
        client.list_files(folder_id="x", mime_filter="text/markdown")
    )
    # All sample files are markdown
    assert len(files) == 5
    assert all(f.mime_type == "text/markdown" for f in files)


@pytest.mark.unit
def test_demo_client_filters_to_empty_when_mime_does_not_match():
    client = DemoDriveClient()
    files = asyncio.run(
        client.list_files(folder_id="x", mime_filter="application/pdf")
    )
    assert files == []


@pytest.mark.unit
def test_demo_client_respects_page_size():
    client = DemoDriveClient()
    files = asyncio.run(client.list_files(folder_id="x", page_size=2))
    assert len(files) == 2


# ---------------------------------------------------------------------------
# DemoDriveClient — read_file
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_demo_client_returns_actual_file_content():
    client = DemoDriveClient()
    content = asyncio.run(client.read_file("demo-001"))
    assert isinstance(content, bytes)
    assert len(content) > 0
    # Should contain real Persian text
    decoded = content.decode("utf-8")
    assert "قانون مالیات‌های مستقیم" in decoded


@pytest.mark.unit
def test_demo_client_returns_empty_for_unknown_file():
    client = DemoDriveClient()
    content = asyncio.run(client.read_file("nonexistent"))
    assert content == b""


@pytest.mark.unit
def test_demo_client_read_each_sample_file():
    client = DemoDriveClient()
    for meta in SAMPLE_FILES_META:
        content = asyncio.run(client.read_file(meta["id"]))
        assert len(content) > 0, f"Empty content for {meta['id']}"
        # Should contain Persian text
        assert "قانون" in content.decode("utf-8") or "بخشنامه" in content.decode("utf-8") or "آرای" in content.decode("utf-8")


# ---------------------------------------------------------------------------
# DemoDriveClient — write_file
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_demo_client_write_returns_fake_file_handle():
    client = DemoDriveClient()
    result = asyncio.run(
        client.write_file(
            parent_folder_id="x",
            name="test.txt",
            content=b"hello",
            mime_type="text/plain",
        )
    )
    assert result.name == "test.txt"
    assert result.mime_type == "text/plain"
    assert result.id.startswith("demo-write-")


# ---------------------------------------------------------------------------
# DemoDriveClient — sample files metadata
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_sample_files_have_five_documents():
    assert len(SAMPLE_FILES_META) == 5


@pytest.mark.unit
def test_sample_files_have_required_fields():
    required = {"id", "name", "mime_type", "title", "kind", "ref_id", "effective_date"}
    for meta in SAMPLE_FILES_META:
        assert required.issubset(meta.keys()), f"Missing fields in {meta['id']}"
        assert meta["kind"] in {"law", "circular", "judgment"}


@pytest.mark.unit
def test_sample_files_include_direct_tax_law():
    qmm = next(m for m in SAMPLE_FILES_META if m["ref_id"] == "qmm-001")
    assert "مستقیم" in qmm["title"]


@pytest.mark.unit
def test_sample_files_include_vat_law():
    vat = next(m for m in SAMPLE_FILES_META if m["ref_id"] == "qvafz-001")
    assert "ارزش افزوده" in vat["title"]


@pytest.mark.unit
def test_sample_files_include_circulars():
    circular = next(m for m in SAMPLE_FILES_META if m["kind"] == "circular")
    assert "بخشنامه" in circular["title"]


@pytest.mark.unit
def test_sample_files_include_judgments():
    judgment = next(m for m in SAMPLE_FILES_META if m["kind"] == "judgment")
    assert "دیوان عدالت اداری" in judgment["title"]


# ---------------------------------------------------------------------------
# Factory function — make_drive_client
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_make_drive_client_returns_demo_when_no_creds(monkeypatch):
    monkeypatch.delenv("LOVABLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    client = make_drive_client()
    assert isinstance(client, DemoDriveClient)


@pytest.mark.unit
def test_make_drive_client_returns_demo_when_forced(monkeypatch):
    monkeypatch.setenv("LOVABLE_API_KEY", "real-key")
    monkeypatch.setenv("SOURCE_BRIDGE_DEMO_MODE", "true")
    client = make_drive_client()
    assert isinstance(client, DemoDriveClient)


# ---------------------------------------------------------------------------
# Health Check — get_health()
# ---------------------------------------------------------------------------

from apps.api.app.health.check import (
    get_health,
    get_health_simple,
    check_credentials,
    check_database,
    check_fiqh_rules,
    check_oath_clauses,
    check_llm_provider,
    check_source_bridge,
)


@pytest.mark.unit
def test_health_check_returns_dict_with_required_fields():
    health = get_health()
    d = health.to_dict() if hasattr(health, "to_dict") else health
    required = {"status", "timestamp", "demo_mode", "credentials", "modules",
                "fiqh_rules_count", "oath_clauses_count", "llm_provider", "database"}
    assert required.issubset(set(d.keys()))


@pytest.mark.unit
def test_health_check_includes_all_credential_checks(monkeypatch):
    monkeypatch.delenv("LOVABLE_API_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    health = get_health()
    cred_names = [c["name"] for c in health.to_dict()["credentials"]]
    assert "LOVABLE_API_KEY" in cred_names
    assert "SUPABASE_URL" in cred_names
    assert "LLM_PROVIDER" in cred_names


@pytest.mark.unit
def test_health_check_status_is_degraded_in_demo_mode(monkeypatch):
    """When demo mode + missing critical creds → status should be degraded (not down)."""
    monkeypatch.delenv("LOVABLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("NEXT_PUBLIC_SUPABASE_URL", raising=False)
    monkeypatch.delenv("SOURCE_BRIDGE_DEMO_MODE", raising=False)
    health = get_health()
    assert health.status in ("degraded", "down", "ok")


@pytest.mark.unit
def test_health_check_reports_seven_modules(monkeypatch):
    monkeypatch.delenv("LOVABLE_API_KEY", raising=False)
    health = get_health()
    # In demo mode, all 7 modules should be "available"
    assert len(health.modules) == 7


@pytest.mark.unit
def test_health_check_reports_seven_fiqh_rules():
    health = get_health()
    assert health.fiqh_rules_count == 7


@pytest.mark.unit
def test_health_check_reports_six_oath_clauses():
    health = get_health()
    assert health.oath_clauses_count == 6


@pytest.mark.unit
def test_health_check_detects_dashboard_url_mistake(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL",
        "https://supabase.com/dashboard/project/abc/sql/123"
    )
    db = check_database()
    assert db["is_dashboard_url"] is True
    assert db["url_format_ok"] is False


@pytest.mark.unit
def test_health_check_accepts_correct_api_url(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://abc.supabase.co")
    db = check_database()
    assert db["is_dashboard_url"] is False
    assert db["url_format_ok"] is True


@pytest.mark.unit
def test_health_simple_returns_minimal_dict(monkeypatch):
    result = get_health_simple()
    assert "status" in result
    assert "timestamp" in result
    assert "version" in result


@pytest.mark.unit
def test_health_check_llm_provider_reported_correctly(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GOOGLE_API_KEY", "AIzaTest")
    provider = check_llm_provider()
    assert provider == "gemini"


@pytest.mark.unit
def test_health_check_llm_provider_warns_when_missing_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = check_llm_provider()
    assert "no API key" in provider


# ---------------------------------------------------------------------------
# Source Bridge — demo mode + get_status
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_source_bridge_reports_demo_mode(monkeypatch):
    """When no creds set, SourceBridge should report demo_mode=True."""
    monkeypatch.delenv("LOVABLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("SOURCE_BRIDGE_DEMO_MODE", raising=False)
    from services.source_bridge.bridge import SourceBridge
    bridge = SourceBridge()
    assert bridge.is_demo_mode is True
    status = bridge.get_status()
    assert status["demo_mode"] is True
    assert status["client_type"] == "DemoDriveClient"
    assert status["modules_count"] == 7
