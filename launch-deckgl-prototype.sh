#!/usr/bin/env bash
# Launch cheias.pt deck.gl prototype for local testing
cd "$(dirname "$0")"
PORT=${1:-8080}
echo ""
echo "  🌊 cheias.pt — deck.gl prototype"
echo "  http://localhost:$PORT/deckgl-prototype.html"
echo ""
echo "  Press Ctrl+C to stop"
echo ""
python3 -m http.server "$PORT" --bind 127.0.0.1
