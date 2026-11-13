#!/usr/bin/env python3
"""Incrementally mirror one private Google Drive case folder.

Examples:
  python scripts/sync_case_drive.py --case-id case-1405-abgin-gostar-toos \
    --folder-id DRIVE_FOLDER_ID --service-account D:/secrets/drive-sa.json
  python scripts/sync_case_drive.py --case-id case-001 --folder-id ID --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "drive-case-sync"
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))
from sync import DriveSyncError, sync_case_folder  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="همگام‌سازی افزایشی پرونده خصوصی از Google Drive")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--folder-id", required=True)
    parser.add_argument("--mirror-root", default=str(ROOT / "data" / "case_drive_mirror"))
    parser.add_argument("--service-account", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = sync_case_folder(
            case_id=args.case_id,
            folder_id=args.folder_id,
            mirror_root=args.mirror_root,
            service_account_json=args.service_account,
            dry_run=args.dry_run,
        )
    except DriveSyncError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, **result.__dict__}, ensure_ascii=False, indent=2))
    return 0 if result.errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
