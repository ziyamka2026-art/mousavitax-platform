import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "drive-case-sync"))
import sync  # noqa: E402
from sync import _safe_relative_path, sync_case_folder  # noqa: E402


def test_safe_relative_path_removes_traversal_and_windows_separators():
    path = _safe_relative_path("../پرونده/..\\تشخیص.pdf")
    assert ".." not in path.parts
    assert path.name.endswith("تشخیص.pdf")


def test_invalid_case_id_is_rejected():
    import re

    assert not re.fullmatch(r"[A-Za-z0-9_-]{3,200}", "case/secret")


def test_sync_downloads_then_skips_unchanged(tmp_path, monkeypatch):
    item = {
        "id": "drive-file-1",
        "name": "تشخیص.pdf",
        "mimeType": "application/pdf",
        "size": "7",
        "md5Checksum": "remote-md5",
        "modifiedTime": "2026-01-01T00:00:00Z",
        "relative_path": "اوراق/تشخیص.pdf",
        "webViewLink": "https://drive.google.com/file/d/drive-file-1",
    }
    monkeypatch.setattr(sync, "_get_service", lambda _: object())
    monkeypatch.setattr(sync, "_iter_files", lambda _service, _folder_id: [item])
    monkeypatch.setattr(sync, "_download", lambda _service, _item: (b"pdf-data", "تشخیص.pdf"))

    first = sync_case_folder(case_id="case-001", folder_id="folder-001", mirror_root=tmp_path)
    assert first.downloaded == 1
    assert first.unchanged == 0
    manifest = json.loads((tmp_path / "case-001" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["files"]["drive-file-1"]["sha256"]
    assert (tmp_path / "case-001" / "اوراق" / "تشخیص.pdf").read_bytes() == b"pdf-data"

    second = sync_case_folder(case_id="case-001", folder_id="folder-001", mirror_root=tmp_path)
    assert second.downloaded == 0
    assert second.updated == 0
    assert second.unchanged == 1
