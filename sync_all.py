#!/usr/bin/env python3
"""Run all bank syncs. cumulus dedupes repeats (date + amount + merchant)."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CHILE_TZ = ZoneInfo("America/Santiago")
ROOT = Path(__file__).resolve().parent
PYTHON = ROOT / ".venv" / "bin" / "python"

BANKS: list[tuple[str, str]] = [
    ("santander", "sync_santander.py"),
    ("edwards", "sync_edwards.py"),
    ("consorcio", "sync_consorcio.py"),
]

PUSH_STATS_RE = re.compile(
    r"appended:\s*(\d+).*?skipped duplicates:\s*(\d+)",
    re.DOTALL,
)


def run_bank(
    name: str,
    script: str,
    *,
    dry_run: bool,
    headless: bool,
) -> dict:
    cmd = [str(PYTHON), str(ROOT / script)]
    if dry_run:
        cmd.append("--dry-run")
    if headless:
        cmd.append("--headless")

    print(f"\n{'=' * 60}")
    print(name)
    print("=" * 60)

    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = proc.stdout
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)

    appended = 0
    skipped = 0
    match = PUSH_STATS_RE.search(output)
    if match:
        appended = int(match.group(1))
        skipped = int(match.group(2))

    return {
        "name": name,
        "ok": proc.returncode == 0,
        "code": proc.returncode,
        "appended": appended,
        "skipped_duplicates": skipped,
    }


def print_summary(results: list[dict], *, dry_run: bool) -> int:
    now = datetime.now(CHILE_TZ).strftime("%Y-%m-%d %H:%M %Z")
    print(f"\n{'=' * 60}")
    print(f"Summary ({now})")
    print("=" * 60)

    failures = 0
    total_appended = 0
    total_skipped = 0

    for result in results:
        status = "ok" if result["ok"] else f"FAILED (exit {result['code']})"
        print(f"  {result['name']:<12} {status}")
        if result["ok"] and not dry_run:
            print(
                f"               appended {result['appended']}, "
                f"skipped duplicates {result['skipped_duplicates']}"
            )
            total_appended += result["appended"]
            total_skipped += result["skipped_duplicates"]
        if not result["ok"]:
            failures += 1

    if not dry_run:
        print(
            f"\nTotal new: {total_appended}  |  "
            f"Total skipped (already in cumulus): {total_skipped}"
        )

    return 1 if failures else 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Santander, Edwards, and Consorcio syncs in sequence"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape and preview only; never push",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browsers headless (often blocked by banks)",
    )
    args = parser.parse_args()

    if not PYTHON.is_file():
        print(f"Missing venv python at {PYTHON}", file=sys.stderr)
        sys.exit(1)

    results: list[dict] = []
    for name, script in BANKS:
        results.append(
            run_bank(name, script, dry_run=args.dry_run, headless=args.headless)
        )

    sys.exit(print_summary(results, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
