#!/usr/bin/env bash
# One-time Pi setup: install dependencies and wire system picamera2/gpiozero into the uv venv.
set -e

echo "→ Running uv sync..."
uv sync

PYVER=$(uv run python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PTH=".venv/lib/python${PYVER}/site-packages/system-dist-packages.pth"

echo "/usr/lib/python3/dist-packages" > "$PTH"
echo "→ Wired system packages into venv (${PTH})"

uv run python -c "from picamera2 import Picamera2; print('✓ picamera2 OK')" 2>/dev/null \
    || echo "⚠ picamera2 not found — install it with: sudo apt install python3-picamera2"

echo "Done. Start the app with:"
echo "  uv run flask --app app:create_app run --host 0.0.0.0 --port 5000"
