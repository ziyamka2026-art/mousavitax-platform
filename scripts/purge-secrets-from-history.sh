#!/usr/bin/env bash
# =============================================================================
# Purge .env.local from Git history — MousaviTax
# =============================================================================
# This script removes .env.local (and other secret files) from the entire Git
# history of the repository. Run once after rotating all exposed secrets.
#
# Usage:
#   bash scripts/purge-secrets-from-history.sh
#
# IMPORTANT:
#   1. Rotate ALL secrets exposed in .env.local BEFORE running this script.
#      (Supabase service role key, anon key, etc.)
#   2. After running, force-push to remote (warn collaborators first).
#   3. Anyone with a clone must re-clone — old commits still contain secrets.
# =============================================================================

set -euo pipefail

# Color helpers
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}=== Purging secret files from Git history ===${NC}"

# Sanity check: ensure we're in a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo -e "${RED}ERROR: Not inside a Git repository.${NC}"
  exit 1
fi

# Files to purge (these were committed at some point)
PURGE_FILES=(
  ".env.local"
  ".env.production"
  ".env.staging"
  ".env.development"
  ".env.test"
  "credentials.json"
  "service-account.json"
  "google-service-account.json"
)

# Build the --path args
PATH_ARGS=()
for f in "${PURGE_FILES[@]}"; do
  PATH_ARGS+=(--path "$f")
done

# Check if git-filter-repo is installed
if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo -e "${YELLOW}git-filter-repo not installed. Installing...${NC}"
  pip install --user git-filter-repo
  export PATH="$HOME/.local/bin:$PATH"
fi

# Run the purge
echo -e "${GREEN}Purging files: ${PURGE_FILES[*]}${NC}"
git filter-repo "${PATH_ARGS[@]}" --invert-paths --force

# Update .gitignore (already done by the senior-review-hardening commit)
echo -e "${GREEN}Verifying .gitignore has .env.local pattern...${NC}"
if ! grep -qE "^\.env\.local$" .gitignore 2>/dev/null; then
  echo ".env.local" >> .gitignore
  echo -e "${YELLOW}Added .env.local to .gitignore${NC}"
fi

echo ""
echo -e "${GREEN}=== Purge complete ===${NC}"
echo ""
echo -e "${YELLOW}NEXT STEPS (DO NOT SKIP):${NC}"
echo ""
echo "  1. Rotate ALL secrets that were ever in .env.local:"
echo "     - Supabase: Project Settings → API → Reset ANON_KEY and SERVICE_ROLE_KEY"
echo "     - OpenAI:   https://platform.openai.com/api-keys → Revoke old keys"
echo "     - Google:   https://console.cloud.google.com/iam/admin/serviceaccounts"
echo "     - Telegram: @BotFather → /revoke → Get new token"
echo ""
echo "  2. Force-push the cleaned history to remote:"
echo "     git push origin main --force"
echo "     git push origin --tags --force"
echo ""
echo "  3. Notify ALL collaborators to re-clone the repository."
echo "     Their existing clones still contain secrets in history."
echo ""
echo "  4. Verify no secrets remain in current files:"
echo "     trufflehog filesystem . --only-verified"
echo ""
