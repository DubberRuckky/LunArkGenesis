#!/usr/bin/env bash
set -e

echo "========================================================"
echo "       LunArk: Genesis - Moon-Base Management"
echo "    NASA Space Apps Challenge 2026 - Team LunArk"
echo "========================================================"
echo ""
echo "Welcome Commander! Preparing lunar outpost environment..."
echo ""

# Find python3 or python
if command -v python3 >/dev/null 2>&1; then
    PY_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PY_BIN="python"
else
    echo "[ERROR] Python 3 not found. Please install Python 3.11+."
    exit 1
fi

# Create virtual environment if not present
if [ ! -f ".venv/bin/activate" ]; then
    echo "[*] Creating virtual environment (.venv)..."
    "$PY_BIN" -m venv .venv
fi

# Activate and install dependencies
echo "[*] Activating virtual environment and verifying requirements..."
# shellcheck source=/dev/null
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo ""
echo "[*] Launching LunArk: Genesis..."
echo "========================================================"
echo ""
python main.py --skip-startup --debug
