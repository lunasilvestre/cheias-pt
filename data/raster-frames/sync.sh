#!/usr/bin/env bash
# Sync pre-rendered map frames (~14MB)
# Subdirs: precipitation/, soil-moisture/
# Usage: ./sync.sh [pull|push] [rclone flags...]
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(git -C "$DIR" rev-parse --show-toplevel)"
REL="${DIR#$ROOT/}"
REMOTE="${CHEIAS_REMOTE:-cheias:cheias-pt}"

case "${1:-pull}" in
  pull) rclone sync "$REMOTE/$REL" "$DIR" --exclude="sync.sh" --progress "${@:2}" ;;
  push) rclone sync "$DIR" "$REMOTE/$REL" --exclude="sync.sh" --progress "${@:2}" ;;
  *) echo "Usage: $0 [pull|push] [rclone flags...]"; exit 1 ;;
esac
