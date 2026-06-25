"""Extract movement rows from Consorcio checking account page."""

from __future__ import annotations

from playwright.sync_api import Page

EXTRACT_CONSORCIO_ROWS_JS = """
() => {
  const table = document.querySelector("cns-table");
  if (!table) return [];

  const flat = [...table.querySelectorAll("div")]
    .map((node) => (node.innerText || "").trim())
    .filter(Boolean);
  const dateRe = /^\\d{2}\\/\\d{2}\\/\\d{4}$/;
  const rows = [];

  for (let index = 0; index < flat.length; index += 1) {
    if (!dateRe.test(flat[index])) continue;
    rows.push(flat.slice(index, index + 6));
    index += 5;
  }

  return rows;
}
"""


def extract_movement_rows(page: Page) -> list[list[str]]:
    return page.evaluate(EXTRACT_CONSORCIO_ROWS_JS)
