"""Private Google Drive case-folder sync endpoints.

Drive remains the source of truth. The endpoint mirrors files to the local
worker volume and records a manifest/history for extraction and auditing.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

API_ROOT = Path(__file__).resolve().parents[3]
SYNC_PACKAGE = API_ROOT / "packages" / "drive-case-sync"
if str(SYNC_PACKAGE) not in sys.path:
    sys.path.insert(0, str(SYNC_PACKAGE))
from sync import DriveSyncError, sync_case_folder  # noqa: E402

router = APIRouter(prefix="/v1/cases", tags=["case-drive"])
MIRROR_ROOT = Path(os.getenv("CASE_DRIVE_MIRROR_ROOT", str(API_ROOT / "data" / "case_drive_mirror")))


class DriveSyncRequest(BaseModel):
    folder_id: str = Field(..., min_length=10, max_length=200)
    dry_run: bool = False
    service_account_json: str | None = None


def _manifest_path(case_id: str) -> Path:
    return MIRROR_ROOT / case_id / "manifest.json"


@router.post("/{case_id}/drive/sync")
async def sync_drive_case(case_id: str, body: DriveSyncRequest) -> dict[str, Any]:
    """Run one incremental sync; use a worker for large folders in production."""
    try:
        result = sync_case_folder(
            case_id=case_id,
            folder_id=body.folder_id,
            mirror_root=MIRROR_ROOT,
            service_account_json=body.service_account_json,
            dry_run=body.dry_run,
        )
    except DriveSyncError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, **result.__dict__}


@router.get("/{case_id}/drive/status")
async def drive_case_status(case_id: str) -> dict[str, Any]:
    path = _manifest_path(case_id)
    if not path.exists():
        return {"ok": True, "case_id": case_id, "status": "not_synced", "files": 0}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"manifest is invalid: {exc}") from exc
    return {
        "ok": True,
        "case_id": case_id,
        "status": "synced",
        "updated_at": manifest.get("updated_at"),
        "drive_folder_id": manifest.get("drive_folder_id"),
        "files": len(manifest.get("files", {})),
        "manifest_path": str(path),
        "history_path": str(path.with_name("sync-history.jsonl")),
    }
