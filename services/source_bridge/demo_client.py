"""
Demo Drive Client — Sample Iranian Tax Laws for Offline Mode
================================================================

Provides canned responses when real Google Drive credentials are not
available. This solves the "0 files" problem in development and the
Lovable preview when Drive integration isn't set up yet.

Activation rules (any one triggers demo mode):
  - LOVABLE_API_KEY is unset
  - GOOGLE_SERVICE_ACCOUNT_JSON is unset
  - SOURCE_BRIDGE_DEMO_MODE == 'true' (force-enable for testing)

The demo data lives in data/sample_laws/ and includes:
  - قانون مالیات‌های مستقیم (with articles 14, 251-m, 252)
  - قانون مالیات بر ارزش افزوده
  - بخشنامه‌های نمونه (230/15254, 200/99/522, 219/20303)
  - آیین‌نامه اجرایی ماده 219
  - آرای منتخب دیوان عدالت اداری

@package services.source_bridge.demo_client
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bridge import DriveFile


# ---------------------------------------------------------------------------
# Sample Drive files — each represents a tax law document
# ---------------------------------------------------------------------------

SAMPLE_FILES_META = [
    {
        "id": "demo-001",
        "name": "001_qanon_maliyat_haye_mostaqim.md",
        "mime_type": "text/markdown",
        "title": "قانون مالیات‌های مستقیم",
        "kind": "law",
        "ref_id": "qmm-001",
        "effective_date": "1966-07-18",  # ۱۳۴۵/۰۴/۲۷
    },
    {
        "id": "demo-002",
        "name": "002_qanon_arzesh_afzoodeh.md",
        "mime_type": "text/markdown",
        "title": "قانون مالیات بر ارزش افزوده",
        "kind": "law",
        "ref_id": "qvafz-001",
        "effective_date": "2007-06-14",  # ۱۳۸۶/۰۳/۲۴
    },
    {
        "id": "demo-003",
        "name": "003_bokhshnameh_nemune.md",
        "mime_type": "text/markdown",
        "title": "بخشنامه‌های نمونه — سازمان امور مالیاتی",
        "kind": "circular",
        "ref_id": "circular-001",
        "effective_date": "2023-04-05",  # ۱۴۰۲/۰۱/۱۵
    },
    {
        "id": "demo-004",
        "name": "004_aeennnameh_ejraei.md",
        "mime_type": "text/markdown",
        "title": "آیین‌نامه اجرایی ماده ۲۱۹ قانون مالیات‌های مستقیم",
        "kind": "law",
        "ref_id": "regulation-219",
        "effective_date": "2007-05-11",  # ۱۳۸۶/۰۲/۲۱
    },
    {
        "id": "demo-005",
        "name": "005_ray_divan_edalat_edari.md",
        "mime_type": "text/markdown",
        "title": "آرای منتخب دیوان عدالت اداری",
        "kind": "judgment",
        "ref_id": "divan-r1",
        "effective_date": "2023-07-01",
    },
]


def _load_sample_content(file_id: str) -> bytes:
    """Load actual file content from data/sample_laws/."""
    # Find the meta entry
    meta = next((m for m in SAMPLE_FILES_META if m["id"] == file_id), None)
    if meta is None:
        return b""

    # Find sample data path
    repo_root = Path(__file__).resolve().parent.parent.parent
    sample_path = repo_root / "data" / "sample_laws" / meta["name"]

    if not sample_path.exists():
        # Fallback to in-memory content
        return f"# {meta['title']}\n\n[Demo content - file not found on disk]\n".encode()

    return sample_path.read_bytes()


# ---------------------------------------------------------------------------
# Demo Drive Client — same interface as GoogleDriveClient
# ---------------------------------------------------------------------------

class DemoDriveClient:
    """
    Test/offline Drive client — returns canned sample tax law files.

    Implements the same async interface as GoogleDriveClient so it can be
    a drop-in replacement when credentials are missing.
    """

    def __init__(self) -> None:
        self._start_time = time.time()
        self._is_demo = True

    def _to_drive_file(self, meta: dict[str, Any]) -> DriveFile:
        return DriveFile(
            id=meta["id"],
            name=meta["name"],
            mime_type=meta["mime_type"],
            web_view_link=f"https://example.com/demo/{meta['id']}",
            modified_time="2026-10-25T10:00:00+00:00",
            size=len(_load_sample_content(meta["id"])),
        )

    async def list_files(
        self,
        folder_id: str,
        mime_filter: str | None = None,
        page_size: int = 100,
    ) -> list[DriveFile]:
        """Return all demo files, optionally filtered by MIME."""
        files = [self._to_drive_file(m) for m in SAMPLE_FILES_META]
        if mime_filter:
            files = [f for f in files if f.mime_type == mime_filter]
        return files[:page_size]

    async def read_file(self, file_id: str, mime_type: str | None = None) -> bytes:
        """Return the actual file bytes from data/sample_laws/."""
        return _load_sample_content(file_id)

    async def write_file(
        self,
        parent_folder_id: str,
        name: str,
        content: bytes,
        mime_type: str = "text/plain",
    ) -> DriveFile:
        """Demo writes are no-ops — return a fake file handle."""
        return DriveFile(
            id=f"demo-write-{int(time.time())}",
            name=name,
            mime_type=mime_type,
        )


# ---------------------------------------------------------------------------
# Factory — picks the right client based on env
# ---------------------------------------------------------------------------

def is_demo_mode() -> bool:
    """Return True if the bridge should run in demo mode."""
    if os.getenv("SOURCE_BRIDGE_DEMO_MODE", "").lower() in ("true", "1", "yes"):
        return True
    # Auto-detect: no credentials → demo mode
    has_lovable = bool(os.getenv("LOVABLE_API_KEY"))
    has_service_account = bool(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
    return not (has_lovable or has_service_account)


def make_drive_client():
    """
    Factory: returns DemoDriveClient or GoogleDriveClient based on env.

    Raises SourceBridgeError only if neither demo nor prod credentials
    are configured — but since demo mode auto-activates on missing creds,
    this should rarely happen.
    """
    if is_demo_mode():
        return DemoDriveClient()
    return _import_real_client()


def _import_real_client():
    """Lazy import to avoid hard dependency when not needed."""
    from .bridge import GoogleDriveClient
    return GoogleDriveClient()


__all__ = [
    "SAMPLE_FILES_META",
    "DemoDriveClient",
    "is_demo_mode",
    "make_drive_client",
]
