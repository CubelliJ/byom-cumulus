#!/bin/bash
# Run all bank syncs with Chile timezone and daily log file.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export TZ=America/Santiago
mkdir -p logs

LOG="logs/sync-$(date +%Y-%m-%d).log"
{
  echo ""
  echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') ==="
  exec "$ROOT/.venv/bin/python" "$ROOT/sync_all.py"
} >>"$LOG" 2>&1
