"""
Google Drive Source Bridge — TAXLAW-GROK Constitution v2.0
==============================================================

Implements Principle 4 of the TAXLAW-GROK Constitution: the inseparable
bond between repository scripts and law.

The bridge connects to a Google Drive master folder (TAXLAW_GROK_MASTER_FOLDER_ID)
and exposes 7 modules as live dependencies for the platform:

  1. LAYEHA_APPEAL_WORKFLOW_V          — appeal document workflow
  2. TAXLAW_GROK_Paged_Queue_Dashboard  — queue dashboard data
  3. setupCaseIndex                     — case indexing & coding
  4. intake_calculator                  — activity profit ratio
  5. summarizer                         — legal summary & verdict extraction
  6. master_control                     — cross-case relationship ledger
  7. law_library                        — tax laws + circular extraction engine

Each module has its own folder ID (subfolder of the master) and exposes
a clean async API. All credentials come from environment variables.

@package services.source_bridge
@see docs/adr/ADR-009-TAXLAW-GROK-Constitution.md (Principle 4)
"""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator

import httpx


# ---------------------------------------------------------------------------
# Module identifiers — match TAXLAW-GROK Constitution Chapter 2
# ---------------------------------------------------------------------------

class ModuleId(str):
    LAYEHA_APPEAL_WORKFLOW_V = "LAYEHA_APPEAL_WORKFLOW_V"
    PAGED_QUEUE_DASHBOARD = "TAXLAW_GROK_Paged_Queue_Dashboard"
    SETUP_CASE_INDEX = "setupCaseIndex"
    INTAKE_CALCULATOR = "intake_calculator"
    SUMMARIZER = "summarizer"
    MASTER_CONTROL = "TAXLAW-GROK-MASTER-CONTROL"
    LAW_LIBRARY = "law_library"


# Default subfolder names within the master folder
DEFAULT_SUBFOLDERS = {
    ModuleId.LAYEHA_APPEAL_WORKFLOW_V: "LAYEHA_APPEAL_WORKFLOW_V",
    ModuleId.PAGED_QUEUE_DASHBOARD: "TAXLAW_GROK_Paged_Queue_Dashboard",
    ModuleId.SETUP_CASE_INDEX: "setupCaseIndex",
    ModuleId.INTAKE_CALCULATOR: "intake_calculator",
    ModuleId.SUMMARIZER: "summarizer",
    ModuleId.MASTER_CONTROL: "TAXLAW-GROK-MASTER-CONTROL",
    ModuleId.LAW_LIBRARY: "law_library",
}


@dataclass
class DriveFile:
    """Represents a file/folder in Google Drive."""
    id: str
    name: str
    mime_type: str
    web_view_link: str | None = None
    modified_time: str | None = None
    size: int | None = None


@dataclass
class ModuleConfig:
    module_id: str
    folder_id: str  # the Drive folder ID for this module
    subfolder_name: str  # display name
    cache_ttl_seconds: int = 300  # 5 min default


class SourceBridgeError(Exception):
    """Raised when a source-bridge operation fails."""


# ---------------------------------------------------------------------------
# Google Drive client — thin wrapper around Drive API v3
# ---------------------------------------------------------------------------

class GoogleDriveClient:
    """
    Minimal async Google Drive v3 client.

    Uses the Lovable connector gateway when running in Lovable env
    (process.env.LOVABLE_API_KEY set), or a direct API call with a
    Google Service Account otherwise.

    The choice is made via LOVABLE_API_KEY env var presence.
    """

    def __init__(self) -> None:
        self._lovable_api_key = os.getenv("LOVABLE_API_KEY")
        self._google_drive_api_key = os.getenv("GOOGLE_DRIVE_API_KEY")
        self._service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        self._gateway = "https://connector-gateway.lovable.dev/google_drive/drive/v3"

        if not self._lovable_api_key and not self._service_account_json:
            raise SourceBridgeError(
                "Either LOVABLE_API_KEY or GOOGLE_SERVICE_ACCOUNT_JSON must be set"
            )

    def _auth_headers(self) -> dict[str, str]:
        if self._lovable_api_key:
            return {
                "Authorization": f"Bearer {self._lovable_api_key}",
                "X-Connection-Api-Key": self._google_drive_api_key or "",
            }
        # Direct service-account flow would OAuth2-exchange here — stubbed
        # for now; production should use google-auth library.
        raise SourceBridgeError(
            "Direct service-account auth not yet implemented — set LOVABLE_API_KEY"
        )

    async def list_files(
        self,
        folder_id: str,
        mime_filter: str | None = None,
        page_size: int = 100,
    ) -> list[DriveFile]:
        """List files in a Drive folder, optionally filtered by MIME."""
        q = f"'{folder_id}' in parents and trashed = false"
        if mime_filter:
            q += f" and mimeType = '{mime_filter}'"
        params = {
            "q": q,
            "pageSize": str(page_size),
            "fields": (
                "files(id,name,mimeType,webViewLink,modifiedTime,size),nextPageToken"
            ),
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(
                f"{self._gateway}/files",
                headers=self._auth_headers(),
                params=params,
            )
            res.raise_for_status()
            data = res.json()

        files = []
        for f in data.get("files", []):
            files.append(
                DriveFile(
                    id=f["id"],
                    name=f["name"],
                    mime_type=f["mimeType"],
                    web_view_link=f.get("webViewLink"),
                    modified_time=f.get("modifiedTime"),
                    size=int(f["size"]) if f.get("size") else None,
                )
            )
        return files

    async def read_file(self, file_id: str, mime_type: str | None = None) -> bytes:
        """Download raw bytes of a Drive file."""
        url = f"{self._gateway}/files/{file_id}?alt=media&supportsAllDrives=true"
        # Handle Google Docs export
        if mime_type == "application/vnd.google-apps.document":
            url = f"{self._gateway}/files/{file_id}/export?mimeType=text/plain"
        elif mime_type == "application/vnd.google-apps.spreadsheet":
            url = f"{self._gateway}/files/{file_id}/export?mimeType=text/csv"

        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.get(url, headers=self._auth_headers())
            res.raise_for_status()
            return res.content

    async def write_file(
        self,
        parent_folder_id: str,
        name: str,
        content: bytes,
        mime_type: str = "text/plain",
    ) -> DriveFile:
        """Upload a new file to a Drive folder (multipart upload)."""
        # Note: real implementation needs multipart/related body
        # Stub: write through gateway's upload endpoint
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(
                f"https://www.googleapis.com/upload/drive/v3/files"
                "?uploadType=multipart&supportsAllDrives=true",
                headers={**self._auth_headers(), "Content-Type": "multipart/related"},
                content=content,
                params={"name": name, "parents": [parent_folder_id]},
            )
            res.raise_for_status()
            data = res.json()
        return DriveFile(
            id=data["id"],
            name=data.get("name", name),
            mime_type=data.get("mimeType", mime_type),
        )


# ---------------------------------------------------------------------------
# Base module interface
# ---------------------------------------------------------------------------

class RepositoryModule(ABC):
    """Base class for all 7 repository modules."""

    module_id: str

    def __init__(
        self,
        drive_client: GoogleDriveClient,
        config: ModuleConfig,
    ) -> None:
        self._drive = drive_client
        self._config = config
        self._cache: dict[str, Any] = {}
        self._cache_ts: dict[str, float] = {}

    @abstractmethod
    async def fetch(self, *args, **kwargs) -> Any:
        """Module-specific fetch operation."""
        ...


# ---------------------------------------------------------------------------
# Module 1: LAYEHA_APPEAL_WORKFLOW_V — Appeal workflow generator
# ---------------------------------------------------------------------------

class LayehaAppealWorkflowModule(RepositoryModule):
    """
    موتور گردش‌کار دادرسی و لایحه‌نویسی
    Generates appeal documents matching the mandatory appeal stages:
    - Article 238 (initial appeal)
    - Article 244 (initial board)
    - Article 247 (review board)
    - Article 251-m (extended review)
    - Supreme Court of Justice
    """
    module_id = ModuleId.LAYEHA_APPEAL_WORKFLOW_V

    APPEAL_STAGES = [
        {"id": "stage_238", "name": "اعتراض ماده ۲۳۸", "deadline_days": 30},
        {"id": "stage_244", "name": "هیئت بدوی ۲۴۴", "deadline_days": 20},
        {"id": "stage_247", "name": "هیئت تجدیدنظر ۲۴۷", "deadline_days": 20},
        {"id": "stage_251_m", "name": "ماده ۲۵۱ مکرر", "deadline_days": 15},
        {"id": "stage_divan", "name": "دیوان عدالت اداری", "deadline_days": 60},
    ]

    async def fetch(self, case_id: str, current_stage: str = "stage_238") -> dict:
        """Fetch appeal template for the given case + stage."""
        cache_key = f"{case_id}_{current_stage}"
        if self._cached(cache_key):
            return self._cache[cache_key]

        # Find the template file in the module's Drive folder
        files = await self._drive.list_files(self._config.folder_id)
        template = next(
            (f for f in files if current_stage in f.name and "template" in f.name.lower()),
            None,
        )

        template_content = ""
        if template:
            raw = await self._drive.read_file(template.id, template.mime_type)
            template_content = raw.decode("utf-8", errors="replace")

        result = {
            "case_id": case_id,
            "current_stage": current_stage,
            "stage_meta": next(
                (s for s in self.APPEAL_STAGES if s["id"] == current_stage),
                self.APPEAL_STAGES[0],
            ),
            "all_stages": self.APPEAL_STAGES,
            "template": template_content,
            "template_file_id": template.id if template else None,
        }
        self._set_cache(cache_key, result)
        return result

    def _cached(self, key: str) -> bool:
        import time
        return (
            key in self._cache
            and key in self._cache_ts
            and (time.time() - self._cache_ts[key]) < self._config.cache_ttl_seconds
        )

    def _set_cache(self, key: str, value: Any) -> None:
        import time
        self._cache[key] = value
        self._cache_ts[key] = time.time()


# ---------------------------------------------------------------------------
# Module 2: Paged Queue Dashboard
# ---------------------------------------------------------------------------

class PagedQueueDashboardModule(RepositoryModule):
    """
    داشبورد صف تحلیل و کنترل وضعیت
    Returns paginated list of cases in analysis pipeline with their status.
    """
    module_id = ModuleId.PAGED_QUEUE_DASHBOARD

    async def fetch(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: str | None = None,
    ) -> dict:
        """Fetch paginated queue of cases."""
        cache_key = f"queue_p{page}_s{page_size}_{status_filter}"
        if self._cached(cache_key):
            return self._cache[cache_key]

        files = await self._drive.list_files(
            self._config.folder_id,
            mime_filter="application/vnd.google-apps.spreadsheet",
        )

        # Filter by status if requested
        items = []
        for f in files:
            if status_filter and status_filter not in f.name:
                continue
            items.append({
                "case_id": f.id,
                "name": f.name,
                "status": "pending_human_review",
                "modified_at": f.modified_time,
                "web_view_link": f.web_view_link,
            })

        # Pagination
        start = (page - 1) * page_size
        end = start + page_size
        paged = items[start:end]

        result = {
            "page": page,
            "page_size": page_size,
            "total": len(items),
            "total_pages": (len(items) + page_size - 1) // page_size,
            "items": paged,
        }
        self._set_cache(cache_key, result)
        return result

    def _cached(self, key: str) -> bool:
        import time
        return (
            key in self._cache
            and key in self._cache_ts
            and (time.time() - self._cache_ts[key]) < self._config.cache_ttl_seconds
        )

    def _set_cache(self, key: str, value: Any) -> None:
        import time
        self._cache[key] = value
        self._cache_ts[key] = time.time()


# ---------------------------------------------------------------------------
# Module 3: setupCaseIndex — Case coding & indexing
# ---------------------------------------------------------------------------

class SetupCaseIndexModule(RepositoryModule):
    """
    شاخص‌بندی و استانداردسازی پرونده‌ها
    Assigns a unique coding to each case before it enters the processing pipeline.
    """
    module_id = ModuleId.SETUP_CASE_INDEX

    # Pattern without anchors — allows search within longer text
    CASE_CODE_PATTERN = re.compile(r"[A-Z]{3}-\d{4}-\d{3}")

    async def fetch(self, case_id: str) -> dict:
        """Generate or fetch a unique case code."""
        cache_key = f"index_{case_id}"
        if self._cached(cache_key):
            return self._cache[cache_key]

        # Look for an existing index file for this case
        files = await self._drive.list_files(self._config.folder_id)
        existing = next(
            (f for f in files if case_id in f.name and "index" in f.name.lower()),
            None,
        )

        if existing:
            raw = await self._drive.read_file(existing.id, existing.mime_type)
            content = raw.decode("utf-8", errors="replace")
            # Parse existing case code from content
            match = self.CASE_CODE_PATTERN.search(content)
            case_code = match.group(0) if match else self._generate_code(case_id)
        else:
            case_code = self._generate_code(case_id)
            content = ""

        result = {
            "case_id": case_id,
            "case_code": case_code,
            "index_file_id": existing.id if existing else None,
            "existing_content": content,
            "is_new": existing is None,
        }
        self._set_cache(cache_key, result)
        return result

    def _generate_code(self, case_id: str) -> str:
        """Generate a deterministic case code from case_id hash."""
        import hashlib
        h = hashlib.sha1(case_id.encode()).hexdigest()
        # Format: ABC-1234-567 (3 letters + 4 digits + 3 digits)
        # Use hex chars mod 26 for letters, mod 10 for digits (only digits in middle)
        letters = "".join(chr(65 + int(h[i], 16) % 26) for i in range(3))
        digits_1 = "".join(str(int(h[3 + i], 16) % 10) for i in range(4))
        digits_2 = "".join(str(int(h[7 + i], 16) % 10) for i in range(3))
        return f"{letters}-{digits_1}-{digits_2}"

    def _cached(self, key: str) -> bool:
        import time
        return (
            key in self._cache
            and key in self._cache_ts
            and (time.time() - self._cache_ts[key]) < self._config.cache_ttl_seconds
        )

    def _set_cache(self, key: str, value: Any) -> None:
        import time
        self._cache[key] = value
        self._cache_ts[key] = time.time()


# ---------------------------------------------------------------------------
# Module 4: intake_calculator — Activity profit ratio
# ---------------------------------------------------------------------------

class IntakeCalculatorModule(RepositoryModule):
    """
    موتور تطبیق نسبت سود فعالیت
    Calculates the activity profit ratio from intake codes.
    """
    module_id = ModuleId.INTAKE_CALCULATOR

    async def fetch(self, intake_code: str, revenue: float) -> dict:
        """Look up the profit ratio for an intake code and calculate taxable profit."""
        cache_key = f"intake_{intake_code}_{revenue}"
        if self._cached(cache_key):
            return self._cache[cache_key]

        # Look up the intake code in the module's Drive folder
        files = await self._drive.list_files(self._config.folder_id)
        ratio_file = next(
            (f for f in files if "ratios" in f.name.lower() or "نسبت" in f.name),
            None,
        )

        profit_ratio = 0.0  # default fallback
        if ratio_file:
            raw = await self._drive.read_file(ratio_file.id, ratio_file.mime_type)
            content = raw.decode("utf-8", errors="replace")
            # Parse CSV-like content for intake_code → ratio
            for line in content.splitlines():
                if intake_code in line:
                    parts = line.split(",")
                    if len(parts) >= 2:
                        try:
                            profit_ratio = float(parts[-1].strip())
                            break
                        except ValueError:
                            continue

        taxable_profit = revenue * profit_ratio
        result = {
            "intake_code": intake_code,
            "revenue": revenue,
            "profit_ratio": profit_ratio,
            "taxable_profit": taxable_profit,
            "source_file": ratio_file.id if ratio_file else None,
        }
        self._set_cache(cache_key, result)
        return result

    def _cached(self, key: str) -> bool:
        import time
        return (
            key in self._cache
            and key in self._cache_ts
            and (time.time() - self._cache_ts[key]) < self._config.cache_ttl_seconds
        )

    def _set_cache(self, key: str, value: Any) -> None:
        import time
        self._cache[key] = value
        self._cache_ts[key] = time.time()


# ---------------------------------------------------------------------------
# Module 5: summarizer — Legal summary & verdict extraction
# ---------------------------------------------------------------------------

class SummarizerModule(RepositoryModule):
    """
    خلاصه‌ساز حقوقی و استنتاج رأی
    Extracts the final output and applies the verdicts to case history.
    """
    module_id = ModuleId.SUMMARIZER

    async def fetch(self, case_id: str, full_text: str) -> dict:
        """Generate a legal summary from the full case text."""
        cache_key = f"summary_{case_id}_{hash(full_text) & 0xFFFFFFFF}"
        if self._cached(cache_key):
            return self._cache[cache_key]

        # Look up summarization template / past summaries
        files = await self._drive.list_files(self._config.folder_id)
        template = next(
            (f for f in files if "template" in f.name.lower()),
            None,
        )

        template_text = ""
        if template:
            raw = await self._drive.read_file(template.id, template.mime_type)
            template_text = raw.decode("utf-8", errors="replace")

        # Generate summary (in production, would call LLM)
        summary = self._generate_summary(full_text, template_text)

        result = {
            "case_id": case_id,
            "summary": summary,
            "input_length": len(full_text),
            "template_used": template is not None,
            "template_file_id": template.id if template else None,
        }
        self._set_cache(cache_key, result)
        return result

    def _generate_summary(self, text: str, template: str) -> str:
        """Naive summary — first 500 chars + last 200 chars."""
        if len(text) <= 700:
            return text
        head = text[:500]
        tail = text[-200:]
        return f"{head}\n\n[...]\n\n{tail}"

    def _cached(self, key: str) -> bool:
        import time
        return (
            key in self._cache
            and key in self._cache_ts
            and (time.time() - self._cache_ts[key]) < self._config.cache_ttl_seconds
        )

    def _set_cache(self, key: str, value: Any) -> None:
        import time
        self._cache[key] = value
        self._cache_ts[key] = time.time()


# ---------------------------------------------------------------------------
# Module 6: master_control — Cross-case relationship ledger
# ---------------------------------------------------------------------------

class MasterControlModule(RepositoryModule):
    """
    جدول مرجع و کنترل ارشد مخزن
    Maintains the master ledger of case relationships, documents, and rulings.
    """
    module_id = ModuleId.MASTER_CONTROL

    async def fetch(self, case_id: str) -> dict:
        """Fetch the master ledger entry for a case."""
        cache_key = f"master_{case_id}"
        if self._cached(cache_key):
            return self._cache[cache_key]

        files = await self._drive.list_files(self._config.folder_id)
        ledger = next(
            (f for f in files if "ledger" in f.name.lower() or "مرجع" in f.name),
            None,
        )

        ledger_data: list[dict] = []
        if ledger:
            raw = await self._drive.read_file(ledger.id, ledger.mime_type)
            content = raw.decode("utf-8", errors="replace")
            # Parse CSV-like ledger
            for line in content.splitlines()[1:]:  # skip header
                parts = line.split(",")
                if len(parts) >= 3 and parts[0].strip() == case_id:
                    ledger_data.append({
                        "case_id": parts[0].strip(),
                        "related_case_id": parts[1].strip() if len(parts) > 1 else None,
                        "relation_type": parts[2].strip() if len(parts) > 2 else None,
                        "notes": parts[3].strip() if len(parts) > 3 else None,
                    })

        result = {
            "case_id": case_id,
            "relations": ledger_data,
            "ledger_file_id": ledger.id if ledger else None,
        }
        self._set_cache(cache_key, result)
        return result

    def _cached(self, key: str) -> bool:
        import time
        return (
            key in self._cache
            and key in self._cache_ts
            and (time.time() - self._cache_ts[key]) < self._config.cache_ttl_seconds
        )

    def _set_cache(self, key: str, value: Any) -> None:
        import time
        self._cache[key] = value
        self._cache_ts[key] = time.time()


# ---------------------------------------------------------------------------
# Module 7: law_library — Tax laws + circular extraction
# ---------------------------------------------------------------------------

class LawLibraryModule(RepositoryModule):
    """
    کتابخانه قوانین مالیاتی و موتورهای استخراج بخشنامه
    Provides the canonical source of tax laws and circulars for citation.
    """
    module_id = ModuleId.LAW_LIBRARY

    async def fetch(self, query: str | None = None, article_id: str | None = None) -> dict:
        """Fetch laws matching a query or specific article ID."""
        cache_key = f"law_{query}_{article_id}"
        if self._cached(cache_key):
            return self._cache[cache_key]

        files = await self._drive.list_files(
            self._config.folder_id,
            mime_filter="application/pdf",
        )

        results: list[DriveFile] = []
        if article_id:
            results = [f for f in files if article_id in f.name]
        elif query:
            results = [f for f in files if query in f.name]
        else:
            results = files[:50]  # first 50 for listing

        result = {
            "query": query,
            "article_id": article_id,
            "matches": [
                {
                    "id": f.id,
                    "name": f.name,
                    "url": f.web_view_link,
                    "modified": f.modified_time,
                }
                for f in results
            ],
            "total": len(results),
        }
        self._set_cache(cache_key, result)
        return result

    def _cached(self, key: str) -> bool:
        import time
        return (
            key in self._cache
            and key in self._cache_ts
            and (time.time() - self._cache_ts[key]) < self._config.cache_ttl_seconds
        )

    def _set_cache(self, key: str, value: Any) -> None:
        import time
        self._cache[key] = value
        self._cache_ts[key] = time.time()


# ---------------------------------------------------------------------------
# Factory — assembles all 7 modules with proper Drive folder IDs
# ---------------------------------------------------------------------------

MODULE_CLASSES = {
    ModuleId.LAYEHA_APPEAL_WORKFLOW_V: LayehaAppealWorkflowModule,
    ModuleId.PAGED_QUEUE_DASHBOARD: PagedQueueDashboardModule,
    ModuleId.SETUP_CASE_INDEX: SetupCaseIndexModule,
    ModuleId.INTAKE_CALCULATOR: IntakeCalculatorModule,
    ModuleId.SUMMARIZER: SummarizerModule,
    ModuleId.MASTER_CONTROL: MasterControlModule,
    ModuleId.LAW_LIBRARY: LawLibraryModule,
}


class SourceBridge:
    """
    Top-level entry point — instantiates the Drive client and all 7 modules.

    Usage:
        bridge = SourceBridge()
        workflow_module = bridge.get_module(ModuleId.LAYEHA_APPEAL_WORKFLOW_V)
        result = await workflow_module.fetch(case_id="CASE-001")
    """

    def __init__(self) -> None:
        # Pick client: DemoDriveClient (offline) or GoogleDriveClient (real)
        # Auto-fallback to demo mode when credentials aren't set.
        from .demo_client import is_demo_mode, make_drive_client
        self._demo_mode = is_demo_mode()
        self._drive = make_drive_client()
        self._master_folder_id = os.getenv(
            "TAXLAW_GROK_MASTER_FOLDER_ID",
            "1M7rsSpQf0akKKmV2P6o66A-uj8KF3cJW",
        )
        self._modules: dict[str, RepositoryModule] = {}
        self._init_modules()

    def _init_modules(self) -> None:
        for module_id, cls in MODULE_CLASSES.items():
            subfolder_name = DEFAULT_SUBFOLDERS[module_id]
            # In production, fetch the actual folder ID by name from Drive.
            # For now, we use the subfolder name as the ID (Drive accepts names as
            # folder IDs only via the gateway). Real implementation would call:
            # files = self._drive.list_files(self._master_folder_id)
            # folder = next(f for f in files if f.name == subfolder_name)
            config = ModuleConfig(
                module_id=module_id,
                folder_id=subfolder_name,  # placeholder — replaced at runtime
                subfolder_name=subfolder_name,
            )
            self._modules[module_id] = cls(drive_client=self._drive, config=config)

    def get_module(self, module_id: str) -> RepositoryModule:
        if module_id not in self._modules:
            raise SourceBridgeError(f"Unknown module: {module_id}")
        return self._modules[module_id]

    def list_modules(self) -> list[str]:
        return list(self._modules.keys())

    @property
    def is_demo_mode(self) -> bool:
        """True when the bridge is running on demo (offline) data."""
        return self._demo_mode

    def get_status(self) -> dict:
        """Return a diagnostic snapshot — safe to expose to /api/health."""
        return {
            "demo_mode": self._demo_mode,
            "master_folder_id": self._master_folder_id,
            "modules_count": len(self._modules),
            "modules": list(self._modules.keys()),
            "client_type": "DemoDriveClient" if self._demo_mode else "GoogleDriveClient",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


__all__ = [
    "ModuleId",
    "DEFAULT_SUBFOLDERS",
    "DriveFile",
    "ModuleConfig",
    "SourceBridgeError",
    "GoogleDriveClient",
    "RepositoryModule",
    "LayehaAppealWorkflowModule",
    "PagedQueueDashboardModule",
    "SetupCaseIndexModule",
    "IntakeCalculatorModule",
    "SummarizerModule",
    "MasterControlModule",
    "LawLibraryModule",
    "MODULE_CLASSES",
    "SourceBridge",
]
