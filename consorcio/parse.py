"""Parse Consorcio checking account rows into cumulus payloads."""

from __future__ import annotations

from common.parse import DateFilter, row_to_movement, today_chile


def parse_movement_rows(
    rows: list[list[str]],
    *,
    date_filter: DateFilter | None = None,
) -> list[dict]:
    today = today_chile()
    date_filter = date_filter or DateFilter.today_only(today)
    movements: list[dict] = []
    seen: set[tuple[str, str, int]] = set()

    for cells in rows:
        if len(cells) < 4:
            continue
        movement = row_to_movement(
            [cells[0], cells[1], cells[3]],
            today=today,
            date_filter=date_filter,
        )
        if not movement:
            continue
        key = (movement["date"], movement["merchant"], movement["amount"])
        if key in seen:
            continue
        seen.add(key)
        movements.append(movement)

    return movements
