#!/usr/bin/env bash
# Sync all data from/to object storage
#
# Usage:
#   ./scripts/sync-data.sh              # pull everything
#   ./scripts/sync-data.sh push         # push everything
#   ./scripts/sync-data.sh pull deploy  # pull only deploy-critical data
#   ./scripts/sync-data.sh pull all     # pull everything (default)
#   ./scripts/sync-data.sh push --dry-run
#
# Configure remote:
#   export CHEIAS_REMOTE="r2:cheias-pt"     # Cloudflare R2
#   export CHEIAS_REMOTE="s3:cheias-pt"     # AWS S3
#   export CHEIAS_REMOTE="cheias:cheias-pt" # default
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ACTION="${1:-pull}"
SCOPE="${2:-all}"

# Deploy-critical data (needed for the website)
DEPLOY_DIRS=(
  data/frontend
  data/consequences
  data/raster-frames
  data/cog
)

# Research data (needed for development/analysis only)
RESEARCH_DIRS=(
  data/temporal
  data/flood-extent
  data/lightning
  data/radar
)

case "$SCOPE" in
  deploy)  DIRS=("${DEPLOY_DIRS[@]}") ;;
  all)     DIRS=("${DEPLOY_DIRS[@]}" "${RESEARCH_DIRS[@]}") ;;
  *)       echo "Unknown scope: $SCOPE (use 'deploy' or 'all')"; exit 1 ;;
esac

FAILED=0
for dir in "${DIRS[@]}"; do
  SYNC="$ROOT/$dir/sync.sh"
  if [[ -x "$SYNC" ]]; then
    echo "=== $dir ($ACTION) ==="
    "$SYNC" "$ACTION" "${@:3}" || { echo "FAILED: $dir"; FAILED=$((FAILED + 1)); }
    echo ""
  else
    echo "SKIP: $dir (no sync.sh)"
  fi
done

if [[ $FAILED -gt 0 ]]; then
  echo "$FAILED sync(s) failed."
  exit 1
fi
echo "Done."
