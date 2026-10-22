from __future__ import annotations

import hashlib
import io
import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".txt", ".md", ".csv", ".png", ".jpg",
    ".jpeg", ".webp", ".tif", ".tiff", ".xlsx", ".xls",
}
GOOGLE_FOLDER = "application/vnd.google-apps.folder"
GOOGLE_EXPORTS = {
    "application/vnd.google-apps.document": ("text/plain", ".txt"),
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"
    ),
}


class DriveSyncError(RuntimeError):
    """A recoverable or actionable Drive synchronization error."""


@dataclass(frozen=True)
class DriveSyncResult:
    case_id: str
    folder_id: str
    mirror_dir: str
    manifest_path: str
    history_path: str
    listed: int
    downloaded: int
    updated: int
    unchanged: int
    skipped: int
    errors: int
    dry_run: bool


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_component(value: str) -> str:
    value = re.sub(r"[\x00-\x1f\x7f]", "_", value or "file")
    value = re.sub(r"[<>:\"/\\|?*]", "_", value)
    value = value.strip().strip(".")
    return value[:180] or "file"


def _safe_relative_path(path: str) -> Path:
    parts = [_safe_component(p) for p in PurePosixPath(path).parts]
    parts = [p for p in parts if p not in {"", ".", ".."}]
    if not parts:
        raise DriveSyncError("Drive returned an empty unsafe path")
    return Path(*parts)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DriveSyncError(f"invalid manifest: {path}: {exc}") from exc


def _write_json(path: Path, value: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _get_service(service_account_json: str | None) -> Any:
    try:
        from google.oauth2 import service_account  # type: ignore
        from googleapiclient.discovery import build  # type: ignore
    except ImportError as exc:
        raise DriveSyncError(
            "Google Drive dependencies are missing. Install "
            "google-api-python-client and google-auth."
        ) from exc
    credentials_path = service_account_json or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not credentials_path:
        raise DriveSyncError("GOOGLE_SERVICE_ACCOUNT_JSON is not configured")
    path = Path(credentials_path).expanduser()
    if not path.exists():
        raise DriveSyncError(f"service account file not found: {path}")
    creds = service_account.Credentials.from_service_account_file(
        str(path), scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _iter_files(service: Any, folder_id: str, prefix: str = "") -> list[dict[str, Any]]:
    q = f"'{folder_id}' in parents and trashed = false"
    result: list[dict[str, Any]] = []
    token: str | None = None
    while True:
        response = service.files().list(
            q=q,
            spaces="drive",
            fields="nextPageToken,files(id,name,mimeType,size,md5Checksum,modifiedTime,webViewLink)",
            pageToken=token,
            pageSize=100,
            orderBy="name",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        for item in response.get("files", []):
            item = dict(item)
            item["relative_path"] = f"{prefix}{item['name']}"
            if item.get("mimeType") == GOOGLE_FOLDER:
                result.extend(_iter_files(service, item["id"], prefix=f"{prefix}{item['name']}/"))
            else:
                result.append(item)
        token = response.get("nextPageToken")
        if not token:
            return result


def _download(service: Any, item: dict[str, Any]) -> tuple[bytes, str]:
    mime = item.get("mimeType", "")
    if mime in GOOGLE_EXPORTS:
        export_mime, suffix = GOOGLE_EXPORTS[mime]
        request = service.files().export_media(fileId=item["id"], mimeType=export_mime)
        effective_name = Path(item["name"]).stem + suffix
    else:
        request = service.files().get_media(fileId=item["id"], supportsAllDrives=True)
        effective_name = item["name"]
    buffer = io.BytesIO()
    from googleapiclient.http import MediaIoBaseDownload  # type: ignore
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue(), effective_name


def sync_case_folder(
    *,
    case_id: str,
    folder_id: str,
    mirror_root: str | Path,
    service_account_json: str | None = None,
    dry_run: bool = False,
) -> DriveSyncResult:
    """Mirror a private Drive folder incrementally.

    The current manifest is rewritten atomically. A separate append-only history
    records every file decision. Local files are never deleted automatically.
    """
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,200}", case_id):
        raise DriveSyncError("case_id must contain only letters, digits, '_' or '-'")
    if not folder_id.strip():
        raise DriveSyncError("folder_id is required")
    mirror = Path(mirror_root).expanduser().resolve() / case_id
    manifest_path = mirror / "manifest.json"
    history_path = mirror / "sync-history.jsonl"
    previous = _load_json(manifest_path).get("files", {})
    service = _get_service(service_account_json)
    items = _iter_files(service, folder_id)
    current: dict[str, Any] = {}
    counts = {"downloaded": 0, "updated": 0, "unchanged": 0, "skipped": 0, "errors": 0}
    if not dry_run:
        mirror.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, Any]] = []
    for item in items:
        raw_name = item.get("relative_path", item.get("name", "file"))
        rel = _safe_relative_path(raw_name)
        ext = Path(item.get("name", "")).suffix.lower()
        mime = item.get("mimeType", "")
        if ext not in ALLOWED_EXTENSIONS and mime not in GOOGLE_EXPORTS:
            counts["skipped"] += 1
            history.append({"at": _now(), "action": "skipped", "reason": "unsupported_type", "file_id": item["id"], "path": str(rel)})
            continue
        old = previous.get(item["id"], {})
        old_path = mirror / old.get("local_path", "") if old.get("local_path") else None
        remote_fingerprint = {
            "modified_time": item.get("modifiedTime"),
            "size": item.get("size"),
            "md5_checksum": item.get("md5Checksum"),
        }
        unchanged = old.get("remote") == remote_fingerprint and bool(old_path and old_path.exists())
        if unchanged:
            current[item["id"]] = {**old, "last_seen_at": _now(), "status": "unchanged"}
            counts["unchanged"] += 1
            history.append({"at": _now(), "action": "unchanged", "file_id": item["id"], "path": str(rel)})
            continue
        if dry_run:
            counts["updated" if old else "downloaded"] += 1
            history.append({"at": _now(), "action": "would_update" if old else "would_download", "file_id": item["id"], "path": str(rel)})
            continue
        try:
            data, effective_name = _download(service, item)
            if effective_name != item.get("name"):
                rel = rel.with_name(_safe_component(effective_name))
            destination = mirror / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            tmp = destination.with_suffix(destination.suffix + ".tmp")
            tmp.write_bytes(data)
            tmp.replace(destination)
            record = {
                "file_id": item["id"],
                "name": item.get("name"),
                "relative_path": raw_name,
                "local_path": str(destination.relative_to(mirror)).replace("\\", "/"),
                "mime_type": item.get("mimeType"),
                "size_bytes": len(data),
                "sha256": _sha256(data),
                "remote": remote_fingerprint,
                "web_view_link": item.get("webViewLink"),
                "first_seen_at": old.get("first_seen_at", _now()),
                "last_seen_at": _now(),
                "status": "updated" if old else "downloaded",
            }
            current[item["id"]] = record
            counts["updated" if old else "downloaded"] += 1
            history.append({"at": _now(), "action": record["status"], "file_id": item["id"], "path": record["local_path"], "sha256": record["sha256"]})
        except Exception as exc:
            counts["errors"] += 1
            history.append({"at": _now(), "action": "error", "file_id": item["id"], "path": str(rel), "error": str(exc)})
    if not dry_run:
        _write_json(manifest_path, {"version": 1, "case_id": case_id, "drive_folder_id": folder_id, "updated_at": _now(), "files": current})
        with history_path.open("a", encoding="utf-8") as stream:
            for record in history:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    return DriveSyncResult(case_id=case_id, folder_id=folder_id, mirror_dir=str(mirror), manifest_path=str(manifest_path), history_path=str(history_path), listed=len(items), dry_run=dry_run, **counts)
