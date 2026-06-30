"""Parse Santander movement rows into cumulus payloads."""

from __future__ import annotations

from common.parse import DateFilter, parse_chilean_date, row_to_movement, today_chile


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


def parse_table_rows(
    rows: list[list[str]],
    *,
    date_filter: DateFilter | None = None,
) -> list[dict]:
    today = today_chile()
    date_filter = date_filter or DateFilter.today_only(today)
    movements: list[dict] = []
    seen: set[tuple[str, str, int]] = set()
    for cells in normalize_santander_rows(rows):
        movement = row_to_movement(cells, today=today, date_filter=date_filter)
        if not movement:
            continue
        key = (movement["date"], movement["merchant"], movement["amount"])
        if key in seen:
            continue
        seen.add(key)
        movements.append(movement)
    return movements
