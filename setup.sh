#!/bin/bash
set -euo pipefail

# ── voice_paste setup ────────────────────────────────────────────────────────
# Creates a venv, installs Python deps, checks system deps.
# Run once: ./setup.sh
# Then:     source venv/bin/activate && python voice_paste.py

PYTHON="/opt/homebrew/bin/python3.13"
VENV_DIR="venv"

echo "[setup] Checking system dependencies ..."

# Check brew packages
missing=()
for pkg in portaudio ffmpeg; do
    if ! brew list "$pkg" &>/dev/null; then
        missing+=("$pkg")
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo "[setup] Installing missing brew packages: ${missing[*]}"
    brew install "${missing[@]}"
else
    echo "[setup] portaudio, ffmpeg — OK"
fi

# Check Python
if [ ! -x "$PYTHON" ]; then
    echo "[setup] ERROR: Python 3.13 not found at $PYTHON"
    echo "        PyTorch does not support Python 3.14 yet."
    echo "        Install with: brew install python@3.13"
    exit 1
fi

echo "[setup] Using $($PYTHON --version)"

# Create venv
if [ -d "$VENV_DIR" ]; then
    echo "[setup] Removing existing venv ..."
    rm -rf "$VENV_DIR"
fi

echo "[setup] Creating venv ..."
$PYTHON -m venv "$VENV_DIR"

echo "[setup] Installing Python packages (this may take a few minutes) ..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet
pip install -r requirements.txt

echo ""
echo "[setup] Done."
echo ""
echo "  To run:"
echo "    source venv/bin/activate"
echo "    python voice_paste.py"
echo ""
echo "  First run will download the Whisper model (~1.6 GB for turbo)."
echo ""
echo "  macOS permissions (one-time):"
echo "    1. Microphone — you'll be prompted automatically on first run"
echo "    2. Accessibility — manually add your terminal app:"
echo "       System Settings → Privacy & Security → Accessibility"
echo ""

