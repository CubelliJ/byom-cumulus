"""Parse Santander credit card movement rows into cumulus payloads."""

from __future__ import annotations

import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

CHILE_TZ = ZoneInfo("America/Santiago")

DATE_RE = re.compile(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})")
CLP_AMOUNT_RE = re.compile(
    r"(?:-\s*)?(?:\$?\s*)(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d{4,})"
)

SKIP_MERCHANT_RE = re.compile(
    r"\b(pago\s+(de\s+)?tarjeta|pago\s+tarjeta|pago\s+minimo|pago\s+deuda|"
    r"cancelacion\s+deuda|abono\s+pago|saldo\s+inicial)\b",
    re.IGNORECASE,
)
CREDIT_MERCHANT_RE = re.compile(
    r"\b(abono|devolucion|reembolso|anulacion|nota\s+de\s+credito)\b",
    re.IGNORECASE,
)


def today_chile() -> date:
    return datetime.now(CHILE_TZ).date()


def parse_chilean_date(raw: str, today: date | None = None) -> date | None:
    match = DATE_RE.search(raw.strip())
    if not match:
        return None
    day, month, year = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    if year < 100:
        year += 2000
    try:
        parsed = date(year, month, day)
    except ValueError:
        return None
    if today and parsed.year != today.year and len(match.group(3)) <= 2:
        # Ambiguous dd/mm/yy around year boundaries.
        parsed = date(today.year, month, day)
    return parsed


def parse_clp_amount(raw: str) -> int | None:
    cleaned = raw.strip().replace("$", "").replace(" ", "")
    negative = cleaned.startswith("-") or cleaned.endswith("-")
    cleaned = cleaned.strip("-")
    if not cleaned:
        return None
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "." in cleaned:
        parts = cleaned.split(".")
        if len(parts) > 1 and all(len(part) == 3 for part in parts[1:]):
            cleaned = "".join(parts)
        else:
            cleaned = cleaned.replace(".", "")
    else:
        cleaned = cleaned.replace(",", "")
    try:
        amount = int(round(float(cleaned)))
    except ValueError:
        return None
    return -amount if negative else amount


def classify_row(merchant: str, signed_amount: int, *, from_abono: bool) -> tuple[bool, bool]:
    """Return (is_credit, should_skip)."""
    if SKIP_MERCHANT_RE.search(merchant):
        return False, True
    if from_abono or signed_amount > 0 or CREDIT_MERCHANT_RE.search(merchant):
        return True, False
    return False, False


def normalize_santander_rows(rows: list[list[str]]) -> list[list[str]]:
    normalized: list[list[str]] = []
    current_date: str | None = None
    for cells in rows:
        cleaned = [cell.strip() for cell in cells if cell and cell.strip()]
        if not cleaned:
            continue
        if cleaned[0].lower() == "fecha":
            continue
        if parse_chilean_date(cleaned[0]):
            current_date = cleaned[0]
            normalized.append([current_date, *cleaned[1:]])
        elif current_date:
            normalized.append([current_date, *cleaned])
    return normalized


def row_to_movement(cells: list[str], today: date | None = None) -> dict | None:
    if len(cells) < 2:
        return None
    today = today or today_chile()

    parsed_date = parse_chilean_date(cells[0], today=today)
    if parsed_date is None or parsed_date != today:
        return None

    amount_hits: list[tuple[int, int, str]] = []
    for idx, cell in enumerate(cells[1:], start=1):
        match = CLP_AMOUNT_RE.search(cell)
        if not match:
            continue
        parsed_amount = parse_clp_amount(match.group(0))
        if parsed_amount is not None and parsed_amount != 0:
            amount_hits.append((idx, parsed_amount, match.group(0)))

    if not amount_hits:
        return None

    if len(amount_hits) >= 2:
        signed_amount, raw_amount_text = amount_hits[-1][1], amount_hits[-1][2]
        from_abono = signed_amount > 0
        amount = abs(signed_amount)
    else:
        signed_amount, raw_amount_text = amount_hits[0][1], amount_hits[0][2]
        from_abono = signed_amount > 0
        amount = abs(signed_amount)

    amount_indices = {hit[0] for hit in amount_hits}
    merchant_parts = [
        cell.strip()
        for i, cell in enumerate(cells)
        if i not in amount_indices and i != 0 and cell.strip()
    ]
    merchant = " ".join(merchant_parts).strip()
    if not merchant:
        return None

    is_credit, skip = classify_row(merchant, signed_amount, from_abono=from_abono)
    if skip:
        return None

    movement = {
        "date": parsed_date.isoformat(),
        "merchant": merchant,
        "amount": amount,
    }
    if is_credit:
        movement["is_credit"] = True
    return movement


def parse_table_rows(rows: list[list[str]], today: date | None = None) -> list[dict]:
    today = today or today_chile()
    movements: list[dict] = []
    seen: set[tuple[str, str, int]] = set()
    for cells in normalize_santander_rows(rows):
        movement = row_to_movement(cells, today=today)
        if not movement:
            continue
        key = (movement["date"], movement["merchant"], movement["amount"])
        if key in seen:
            continue
        seen.add(key)
        movements.append(movement)
    return movements
