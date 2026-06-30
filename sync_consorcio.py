#!/usr/bin/env python3
"""Sync today's Consorcio checking account movements into cumulus."""

from __future__ import annotations

import argparse
import sys

from playwright.sync_api import sync_playwright

from push import load_token, push
from common.browser import BrowserMode, add_browser_args, browser_mode_from_args, launch_browser, save_debug_screenshot
from common.cli import add_date_filter_args, confirm_push, date_filter_from_args, preview_movements
from common.parse import DateFilter
from consorcio.auth import login
from consorcio.navigate import go_to_account_movements
from consorcio.parse import parse_movement_rows
from consorcio.scrape import extract_movement_rows


def run_sync(
    *,
    mode: BrowserMode,
    dry_run: bool,
    confirm: bool,
    inspect: bool,
    date_filter: DateFilter,
) -> None:
    with sync_playwright() as playwright:
        browser, context = launch_browser(playwright, mode=mode)
        page = context.new_page()
        try:
            print("Logging in to Consorcio...")
            page = login(page)
            print("Navigating to account movements...")
            go_to_account_movements(page)
            print("Scraping movements...")

            if inspect:
                print("\n--- page snapshot ---")
                print(page.url)
                print(page.locator("body").inner_text()[:4000])
                print("--- end snapshot ---\n")

            raw_rows = extract_movement_rows(page)
        except Exception as exc:
            save_debug_screenshot(page)
            print(f"Sync failed: {exc}", file=sys.stderr)
            print("Saved screenshot to debug/last-failure.png", file=sys.stderr)
            sys.exit(1)
        finally:
            browser.close()

    movements = parse_movement_rows(raw_rows, date_filter=date_filter)
    preview_movements(
        movements,
        date_filter=date_filter,
        empty_message="(none found on the current page)",
    )

    if dry_run:
        print("\nDry run — nothing pushed.")
        return

    if confirm and not confirm_push(len(movements)):
        print("Cancelled.")
        return

    if not movements:
        print("\nNo movements to push.")
        return

    try:
        result = push(movements, load_token())
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    print(f"\nappended: {result.get('push_appended', 0)}")
    print(f"skipped duplicates: {result.get('push_skipped_duplicates', 0)}")
    print(f"pending total: {result.get('pending_count', 0)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Log into Consorcio, scrape today's account movements, push to cumulus"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape and preview only; never push",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Ask before pushing to cumulus",
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="Print page text after navigation (for tuning selectors)",
    )
    add_browser_args(parser)
    add_date_filter_args(parser)
    args = parser.parse_args()

    run_sync(
        mode=browser_mode_from_args(args),
        dry_run=args.dry_run,
        confirm=args.confirm,
        inspect=args.inspect,
        date_filter=date_filter_from_args(args),
    )


if __name__ == "__main__":
    main()
