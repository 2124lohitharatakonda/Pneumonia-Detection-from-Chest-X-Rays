#!/usr/bin/env bash
# ============================================================
# PneumoDetect — Linux/Mac Production Start Script (Gunicorn)
# Run from project root: bash deployment/start_linux.sh
# ============================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "Starting PneumoDetect from: $PROJECT_DIR"

# Activate virtual environment
if [ ! -f "venv/bin/activate" ]; then
  echo "ERROR: Virtual environment not found. Run: python3 -m venv venv && pip install -r requirements.txt"
  exit 1
fi
# shellcheck disable=SC1091
source venv/bin/activate

# Check .env
if [ ! -f ".env" ]; then
  echo "ERROR: .env file not found. Copy .env.example to .env and configure."
  exit 1
fi

export FLASK_ENV=production

# Create log directory
mkdir -p logs

echo "Launching Gunicorn..."
exec gunicorn -c deployment/gunicorn.conf.py wsgi:app
