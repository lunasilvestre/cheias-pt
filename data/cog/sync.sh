#!/usr/bin/env bash
# Sync all Cloud-Optimized GeoTIFFs (~722MB)
# Subdirs: precipitation, soil-moisture, precondition, ecmwf-hres,
#          satellite-vis, satellite-ir, wind-u, wind-v, wind-gust,
#          mslp, ivt, sst, arpege
# Usage: ./sync.sh [pull|push] [rclone flags...]
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(git -C "$DIR" rev-parse --show-toplevel)"
REL="${DIR#$ROOT/}"
REMOTE="${CHEIAS_REMOTE:-cheias:cheias-pt}"

case "${1:-pull}" in
  pull) rclone sync "$REMOTE/$REL" "$DIR" --exclude="sync.sh" --exclude="*.aux.xml" --progress "${@:2}" ;;
  push) rclone sync "$DIR" "$REMOTE/$REL" --exclude="sync.sh" --exclude="*.aux.xml" --progress "${@:2}" ;;
  *) echo "Usage: $0 [pull|push] [rclone flags...]"; exit 1 ;;
esac
