#!/usr/bin/env python3
"""Push bank movements to cumulus via the BYOM API."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

API_URL = "https://api.trycumulus.com/imports/push"


def load_token() -> str:
    load_dotenv()
    token = os.getenv("CUMULUS_API_KEY") or os.getenv("CUMULUS_TOKEN")
    if not token:
        print(
            "Missing token. Set CUMULUS_API_KEY or CUMULUS_TOKEN in .env",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def movement_from_args(args: argparse.Namespace) -> dict:
    movement: dict = {
        "date": args.date,
        "merchant": args.merchant,
        "amount": args.amount,
    }
    if args.credit:
        movement["is_credit"] = True
    if args.bucket_type:
        movement["bucket_type"] = args.bucket_type
    if args.category:
        movement["category"] = args.category
    return movement


def load_movements_from_file(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "movements" in data:
        return data["movements"]
    raise ValueError('JSON file must be a list of movements or {"movements": [...]}')


def push(movements: list[dict], token: str | None = None) -> dict:
    if token is None:
        token = load_token()
    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"movements": movements},
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(f"Error {response.status_code}: {response.text}")
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Push movements to cumulus")
    parser.add_argument("--file", "-f", type=Path, help="JSON file with movements")
    parser.add_argument("--date", help="YYYY-MM-DD")
    parser.add_argument("--merchant", help="Payee or description")
    parser.add_argument("--amount", type=int, help="Positive amount in CLP")
    parser.add_argument("--credit", action="store_true", help="Mark as income/credit")
    parser.add_argument(
        "--bucket-type", choices=["needs", "wants"], help="Pre-fill bucket"
    )
    parser.add_argument(
        "--category", choices=["food", "transport"], help="Pre-fill category (needs)"
    )
    args = parser.parse_args()

    if args.file:
        movements = load_movements_from_file(args.file)
    elif args.date and args.merchant and args.amount is not None:
        movements = [movement_from_args(args)]
    else:
        parser.error("Provide --file or --date, --merchant, and --amount")

    if not movements:
        print("No movements to push", file=sys.stderr)
        sys.exit(1)

    try:
        result = push(movements, load_token())
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    print(f"appended: {result.get('push_appended', 0)}")
    print(f"skipped duplicates: {result.get('push_skipped_duplicates', 0)}")
    print(f"pending total: {result.get('pending_count', 0)}")


if __name__ == "__main__":
    main()
