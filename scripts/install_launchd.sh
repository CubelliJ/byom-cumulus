#!/bin/bash
# Install launchd job: all banks every 4 hours (Chile local time).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SRC="$ROOT/scripts/com.byom-cumulus.sync.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.byom-cumulus.sync.plist"

chmod +x "$ROOT/scripts/run_sync_all.sh"
mkdir -p "$ROOT/logs"

sed "s|REPLACE_WITH_REPO_PATH|$ROOT|g" "$PLIST_SRC" >"$PLIST_DST"

launchctl bootout "gui/$(id -u)/com.byom-cumulus.sync" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl enable "gui/$(id -u)/com.byom-cumulus.sync"

echo "Installed $PLIST_DST"
echo "Runs at 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 (America/Santiago)."
echo "Logs: $ROOT/logs/sync-YYYY-MM-DD.log"
echo "Browser: unattended (off-screen). Sync uses osascript so launchd works from any clone path."
