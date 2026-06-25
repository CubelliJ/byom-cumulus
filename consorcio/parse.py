"""Parse Consorcio checking account rows into cumulus payloads."""

from __future__ import annotations

from datetime import date

from santander.parse import row_to_movement, today_chile


def parse_movement_rows(rows: list[list[str]], today: date | None = None) -> list[dict]:
    today = today or today_chile()
    movements: list[dict] = []
    seen: set[tuple[str, str, int]] = set()

    for cells in rows:
        if len(cells) < 4:
            continue
        movement = row_to_movement([cells[0], cells[1], cells[3]], today=today)
        if not movement:
            continue
        key = (movement["date"], movement["merchant"], movement["amount"])
        if key in seen:
            continue
        seen.add(key)
        movements.append(movement)

    return movements
