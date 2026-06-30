"""Shared CLP/date parsing for all bank syncs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

CHILE_TZ = ZoneInfo("America/Santiago")

DATE_RE = re.compile(r"(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?")
CLP_AMOUNT_RE = re.compile(
    r"(?:-\s*)?(?:\$?\s*)(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d{4,})"
)

SKIP_MERCHANT_RE = re.compile(
    r"\b(pago\s+(de\s+)?tarjeta|pago\s+tarjeta|pago\s+minimo|pago\s+deuda|"
    r"cancelacion\s+deuda|abono\s+pago|saldo\s+inicial|"
    r"traspaso\s+internet\s+a\s+t\.?\s*cr[eé]dito)\b",
    re.IGNORECASE,
)
CREDIT_MERCHANT_RE = re.compile(
    r"\b(abono|devolucion|reembolso|anulacion|nota\s+de\s+credito)\b",
    re.IGNORECASE,
)


def today_chile() -> date:
    return datetime.now(CHILE_TZ).date()


@dataclass(frozen=True)
class DateFilter:
    """Default: today only in Chile. Use since/until for a range."""

    on_date: date | None = None
    since: date | None = None
    until: date | None = None

    @classmethod
    def today_only(cls, ref: date | None = None) -> DateFilter:
        day = ref or today_chile()
        return cls(on_date=day)

    @classmethod
    def last_month(cls, ref: date | None = None) -> DateFilter:
        end = ref or today_chile()
        # Banks sometimes post with tomorrow's date (e.g. ATM giros on 30/06 while still 29/06).
        return cls(since=end - timedelta(days=30), until=end + timedelta(days=1))

    def allows(self, movement_date: date) -> bool:
        if self.since is not None or self.until is not None:
            if self.since is not None and movement_date < self.since:
                return False
            if self.until is not None and movement_date > self.until:
                return False
            return True
        target = self.on_date or today_chile()
        return movement_date == target

    def label(self) -> str:
        if self.since is not None or self.until is not None:
            start = self.since.isoformat() if self.since else "…"
            end = self.until.isoformat() if self.until else "…"
            return f"{start} → {end}"
        return (self.on_date or today_chile()).isoformat()


def parse_chilean_date(raw: str, today: date | None = None) -> date | None:
    today = today or today_chile()
    match = DATE_RE.fullmatch(raw.strip()) or DATE_RE.search(raw.strip())
    if not match:
        return None
    day, month = int(match.group(1)), int(match.group(2))
    year_text = match.group(3)
    if year_text:
        year = int(year_text)
        if year < 100:
            year += 2000
    else:
        year = today.year
    try:
        parsed = date(year, month, day)
    except ValueError:
        return None
    if year_text and len(year_text) <= 2 and today and parsed.year != today.year:
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


def _pick_movement_amount(
    amount_hits: list[tuple[int, int, str]],
) -> tuple[int, str, bool] | None:
    signed_hits = [
        (idx, amount, raw)
        for idx, amount, raw in amount_hits
        if "-" in raw or "+" in raw
    ]
    if signed_hits:
        _, signed_amount, raw_amount_text = signed_hits[0]
        return signed_amount, raw_amount_text, signed_amount > 0
    if amount_hits:
        _, signed_amount, raw_amount_text = amount_hits[0]
        return signed_amount, raw_amount_text, signed_amount > 0
    return None


def classify_row(merchant: str, signed_amount: int, *, from_abono: bool) -> tuple[bool, bool]:
    """Return (is_credit, should_skip)."""
    if SKIP_MERCHANT_RE.search(merchant):
        return False, True
    if from_abono or signed_amount > 0 or CREDIT_MERCHANT_RE.search(merchant):
        return True, False
    return False, False


def row_to_movement(
    cells: list[str],
    *,
    today: date | None = None,
    date_filter: DateFilter | None = None,
) -> dict | None:
    if len(cells) < 2:
        return None
    today = today or today_chile()
    date_filter = date_filter or DateFilter.today_only(today)

    parsed_date = parse_chilean_date(cells[0], today=today)
    if parsed_date is None or not date_filter.allows(parsed_date):
        return None

    amount_hits: list[tuple[int, int, str]] = []
    for idx, cell in enumerate(cells[1:], start=1):
        if "$" not in cell:
            continue
        match = CLP_AMOUNT_RE.search(cell)
        if not match:
            continue
        parsed_amount = parse_clp_amount(match.group(0))
        if parsed_amount is not None and parsed_amount != 0:
            amount_hits.append((idx, parsed_amount, match.group(0)))

    if not amount_hits:
        return None

    picked = _pick_movement_amount(amount_hits)
    if picked is None:
        return None
    signed_amount, raw_amount_text, from_abono = picked
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


def merge_movements(*groups: list[dict]) -> list[dict]:
    merged: list[dict] = []
    seen: set[tuple[str, str, int]] = set()
    for movements in groups:
        for movement in movements:
            key = (movement["date"], movement["merchant"], movement["amount"])
            if key in seen:
                continue
            seen.add(key)
            merged.append(movement)
    return merged
