"""
Make scripts executable and verify directory structure.

Run:  python scripts/post_install_check.py
"""
import os
import stat
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent

    # Make all shell scripts in scripts/ executable
    scripts_dir = root / "scripts"
    if scripts_dir.exists():
        for script in scripts_dir.iterdir():
            if script.suffix == ".sh":
                mode = os.stat(script).st_mode
                os.chmod(script, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                print(f"  chmod +x {script.relative_to(root)}")

    print()
    print("✅ Post-install check complete.")
    print()

    # Verify expected directories exist
    expected_dirs = [
        "apps/api", "apps/web", "apps/mka-core",
        "packages/auth", "packages/audit", "packages/observability",
        "services/rag",
        "infra/postgres/migrations",
        "tests/unit", "tests/integration", "tests/e2e",
        "docs", "docs/adr", "docs/ops",
    ]
    print("Directory structure:")
    all_ok = True
    for d in expected_dirs:
        path = root / d
        if path.exists():
            print(f"  ✅ {d}")
        else:
            print(f"  ❌ {d} (missing)")
            all_ok = False

    # Verify critical files
    expected_files = [
        ".env.example", ".gitignore", "README.md", "LICENSE",
        "SECURITY.md", "CONTRIBUTING.md",
        "vercel.json", "pyproject.toml", "vitest.config.ts", "tsconfig.json",
        "package.json", "conftest.py", "pytest.ini",
        ".github/workflows/ci.yml",
        "infra/postgres/migrations/001_tenants.sql",
        "infra/postgres/migrations/002_audit_logs.sql",
        "infra/postgres/migrations/003_knowledge_documents.sql",
        "infra/postgres/migrations/004_add_tenant_rls.sql",
        "packages/auth/src/rbac.ts",
        "packages/audit/src/logger.ts",
        "packages/observability/src/index.ts",
        "apps/api/app/llm/factory.py",
        "services/rag/vector_store.py",
        "tests/unit/rbac.test.ts",
        "tests/unit/audit.test.ts",
        "tests/unit/test_rbac.py",
        "tests/unit/test_llm_factory.py",
        "tests/unit/test_vector_store.py",
    ]
    print()
    print("Critical files:")
    for f in expected_files:
        path = root / f
        if path.exists():
            print(f"  ✅ {f}")
        else:
            print(f"  ❌ {f} (missing)")
            all_ok = False

    print()
    if all_ok:
        print("🎉 All expected files and directories are present.")
        return 0
    else:
        print("⚠️  Some expected files are missing. Check above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
