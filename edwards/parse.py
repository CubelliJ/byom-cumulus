"""Parse Edwards checking and credit card rows into cumulus payloads."""

from __future__ import annotations

from datetime import date

from common.parse import (
    DateFilter,
    classify_row,
    merge_movements,
    parse_chilean_date,
    parse_clp_amount,
    today_chile,
)


def _clp_from_cell(cell: str) -> int | None:
    if "$" not in cell:
        return None
    amount = parse_clp_amount(cell)
    if amount is None:
        return None
    return abs(amount)


def _movement_from_parts(
    *,
    parsed_date: date,
    merchant: str,
    amount: int,
    is_credit: bool,
) -> dict | None:
    signed = amount if is_credit else -amount
    credit, skip = classify_row(merchant, signed, from_abono=is_credit)
    if skip:
        return None
    movement = {
        "date": parsed_date.isoformat(),
        "merchant": merchant,
        "amount": amount,
    }
    if credit:
        movement["is_credit"] = True
    return movement


def checking_row_to_movement(
    cells: list[str],
    *,
    today: date | None = None,
    date_filter: DateFilter | None = None,
) -> dict | None:
    if len(cells) < 5:
        return None
    today = today or today_chile()
    date_filter = date_filter or DateFilter.today_only(today)

    parsed_date = parse_chilean_date(cells[0], today=today)
    if parsed_date is None or not date_filter.allows(parsed_date):
        return None

    merchant = cells[1].strip()
    if not merchant or merchant.lower() == "descripción":
        return None

    cargo = _clp_from_cell(cells[3]) if len(cells) > 3 else None
    abono = _clp_from_cell(cells[4]) if len(cells) > 4 else None
    if abono:
        return _movement_from_parts(
            parsed_date=parsed_date,
            merchant=merchant,
            amount=abono,
            is_credit=True,
        )
    if cargo:
        return _movement_from_parts(
            parsed_date=parsed_date,
            merchant=merchant,
            amount=cargo,
            is_credit=False,
        )
    return None


def card_row_to_movement(
    cells: list[str],
    *,
    today: date | None = None,
    date_filter: DateFilter | None = None,
) -> dict | None:
    if len(cells) < 6:
        return None
    today = today or today_chile()
    date_filter = date_filter or DateFilter.today_only(today)

    parsed_date = parse_chilean_date(cells[0], today=today)
    if parsed_date is None or not date_filter.allows(parsed_date):
        return None

    merchant = cells[2].strip() if len(cells) > 2 else ""
    if not merchant or merchant.lower() == "descripción":
        return None

    cargo = _clp_from_cell(cells[5]) if len(cells) > 5 else None
    pago = _clp_from_cell(cells[6]) if len(cells) > 6 else None
    if pago:
        return None
    if not cargo:
        return None

    return _movement_from_parts(
        parsed_date=parsed_date,
        merchant=merchant,
        amount=cargo,
        is_credit=False,
    )


def parse_checking_rows(
    rows: list[list[str]],
    *,
    date_filter: DateFilter | None = None,
) -> list[dict]:
    today = today_chile()
    date_filter = date_filter or DateFilter.today_only(today)
    movements: list[dict] = []
    seen: set[tuple[str, str, int]] = set()
    for cells in rows:
        movement = checking_row_to_movement(
            cells, today=today, date_filter=date_filter
        )
        if not movement:
            continue
        key = (movement["date"], movement["merchant"], movement["amount"])
        if key in seen:
            continue
        seen.add(key)
        movements.append(movement)
    return movements


def parse_card_rows(
    rows: list[list[str]],
    *,
    date_filter: DateFilter | None = None,
) -> list[dict]:
    today = today_chile()
    date_filter = date_filter or DateFilter.today_only(today)
    movements: list[dict] = []
    seen: set[tuple[str, str, int]] = set()
    for cells in rows:
        movement = card_row_to_movement(cells, today=today, date_filter=date_filter)
        if not movement:
            continue
        key = (movement["date"], movement["merchant"], movement["amount"])
        if key in seen:
            continue
        seen.add(key)
        movements.append(movement)
    return movements


__all__ = [
    "parse_card_rows",
    "parse_checking_rows",
]
