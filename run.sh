#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -f ".venv/bin/activate" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt -q

echo ""
echo "=== Running main.py ==="
python main.py
