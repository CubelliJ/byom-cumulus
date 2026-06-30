"""Shared DOM extraction helpers for bank movement tables."""

from __future__ import annotations

from playwright.sync_api import Page

EXTRACT_TABLE_ROWS_JS = """
() => {
  const rows = [];
  const seen = new Set();

  const pushRow = (cells) => {
    const normalized = cells.map((c) => c.replace(/\\s+/g, " ").trim()).filter(Boolean);
    if (normalized.length < 2) return;
    const key = normalized.join("|");
    if (seen.has(key)) return;
    seen.add(key);
    rows.push(normalized);
  };

  for (const table of document.querySelectorAll("table")) {
    for (const tr of table.querySelectorAll("tr")) {
      const cells = [...tr.querySelectorAll("th, td")].map((el) => el.innerText || "");
      pushRow(cells);
    }
  }

  for (const row of document.querySelectorAll("[role='row']")) {
    const cells = [...row.querySelectorAll("[role='cell'], [role='gridcell'], td, th")]
      .map((el) => el.innerText || "");
    pushRow(cells);
  }

  return rows;
}
"""


def extract_table_rows(page: Page) -> list[list[str]]:
    return page.evaluate(EXTRACT_TABLE_ROWS_JS)
