"""Navigate Consorcio to checking account movements."""

from __future__ import annotations

from playwright.sync_api import Page

from consorcio.config import DEFAULT_TIMEOUT_MS, MOVEMENTS_URL


def go_to_account_movements(page: Page) -> None:
    page.get_by_text("Saldos y Movimientos", exact=True).first.click()
    page.wait_for_url(MOVEMENTS_URL, timeout=DEFAULT_TIMEOUT_MS)
    page.wait_for_timeout(3000)
    page.locator("cns-table").first.wait_for(state="visible", timeout=DEFAULT_TIMEOUT_MS)
