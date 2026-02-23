#!/bin/bash
# cheias.pt — Local development server
# Usage: ./scripts/serve.sh [port]
#
# Serves the project root with correct MIME types for ES modules.
# Falls back from Node (npx serve) → Python 3 http.server.

PORT=${1:-3000}
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🌊 cheias.pt — local dev server"
echo "   Root: $ROOT"
echo "   Port: $PORT"
echo ""

# Try npx serve first (better MIME type handling for ES modules)
if command -v npx &> /dev/null; then
  echo "→ Using npx serve"
  echo "  http://localhost:$PORT"
  echo ""
  cd "$ROOT" && npx serve -l $PORT -s --no-clipboard
elif command -v python3 &> /dev/null; then
  echo "→ Using Python 3 http.server"
  echo "  http://localhost:$PORT"
  echo ""
  cd "$ROOT" && python3 -m http.server $PORT
else
  echo "❌ Need either Node.js (npx) or Python 3 to serve."
  exit 1
fi
