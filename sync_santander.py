#!/usr/bin/env python3
"""Sync today's Santander checking and credit card movements into cumulus."""

from __future__ import annotations

import argparse
import sys

from playwright.sync_api import sync_playwright

from push import load_token, push
from santander.auth import login
from santander.browser import launch_browser, save_debug_screenshot
from santander.navigate import go_to_checking_movements, go_to_credit_card_movements
from santander.parse import merge_movements, parse_table_rows, today_chile
from santander.scrape import extract_movement_rows


def preview_movements(movements: list[dict]) -> None:
    print(f"\nToday's movements ({today_chile().isoformat()}):\n")
    if not movements:
        print("  (none found)")
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
            print("Logging in to Santander...")
            page = login(page)

            print("Navigating to checking account movements...")
            go_to_checking_movements(page)
            checking_rows = extract_movement_rows(page)
            checking_movements = parse_table_rows(checking_rows)
            print(f"  checking: {len(checking_movements)} today")

            print("Navigating to credit card movements...")
            go_to_credit_card_movements(page)
            card_rows = extract_movement_rows(page)
            card_movements = parse_table_rows(card_rows)
            print(f"  credit card: {len(card_movements)} today")

            if inspect:
                print("\n--- credit card page snapshot ---")
                print(page.url)
                print(page.locator("body").inner_text()[:4000])
                print("--- end snapshot ---\n")

            movements = merge_movements(checking_movements, card_movements)
        except Exception as exc:
            save_debug_screenshot(page)
            print(f"Sync failed: {exc}", file=sys.stderr)
            print("Saved screenshot to debug/last-failure.png", file=sys.stderr)
            sys.exit(1)
        finally:
            browser.close()

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
        description="Log into Santander, scrape today's account and TC movements, push to cumulus"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser headless (may be blocked by Santander)",
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
