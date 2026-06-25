#!/usr/bin/env python3
"""Sync today's Consorcio checking account movements into cumulus."""

from __future__ import annotations

import argparse
import sys

from playwright.sync_api import sync_playwright

from consorcio.auth import login
from consorcio.navigate import go_to_account_movements
from consorcio.parse import parse_movement_rows
from consorcio.scrape import extract_movement_rows
from push import load_token, push
from santander.browser import launch_browser, save_debug_screenshot
from santander.parse import today_chile


def preview_movements(movements: list[dict]) -> None:
    print(f"\nToday's movements ({today_chile().isoformat()}):\n")
    if not movements:
        print("  (none found on the current page)")
        return
    for idx, movement in enumerate(movements, start=1):
        kind = "credit" if movement.get("is_credit") else "expense"
        print(
            f"  {idx}. {movement['date']}  {movement['merchant'][:50]:<50}  "
            f"${movement['amount']:,}  ({kind})"
        )


def confirm_push(count: int) -> bool:
    if count == 0:
        return False
    answer = input(f"\nPush {count} movement(s) to cumulus? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def run_sync(*, headless: bool, dry_run: bool, confirm: bool, inspect: bool) -> None:
    with sync_playwright() as playwright:
        browser, context = launch_browser(playwright, headless=headless)
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

    movements = parse_movement_rows(raw_rows)
    preview_movements(movements)

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
        "--headless",
        action="store_true",
        help="Run browser headless (may be blocked by Consorcio)",
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
    args = parser.parse_args()

    run_sync(
        headless=args.headless,
        dry_run=args.dry_run,
        confirm=args.confirm,
        inspect=args.inspect,
    )


if __name__ == "__main__":
    main()
