"""Shared CLI helpers for sync orchestrators."""

from __future__ import annotations

import argparse
from datetime import date

from common.parse import DateFilter, today_chile


def add_date_filter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--last-month",
        action="store_true",
        help="Include movements from the last 30 days through tomorrow (debug; banks may post ahead)",
    )
    parser.add_argument(
        "--since",
        type=date.fromisoformat,
        metavar="YYYY-MM-DD",
        help="Include movements on or after this date (debug)",
    )


def date_filter_from_args(args) -> DateFilter:
    if args.since is not None:
        return DateFilter(since=args.since, until=today_chile())
    if args.last_month:
        return DateFilter.last_month()
    return DateFilter.today_only()


def preview_movements(
    movements: list[dict],
    *,
    date_filter: DateFilter | None = None,
    empty_message: str = "(none found)",
) -> None:
    date_filter = date_filter or DateFilter.today_only()
    print(f"\nMovements ({date_filter.label()}):\n")
    if not movements:
        print(f"  {empty_message}")
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


def dump_page_snapshot(page, label: str, *, limit: int = 8000) -> None:
    print(f"\n--- {label} ---")
    print(page.url)
    text = page.evaluate("() => document.body?.innerText || ''")
    print(text[:limit])
    print("--- end snapshot ---\n")
