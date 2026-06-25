"""Navigate Santander private site to credit card movements."""

from __future__ import annotations

from playwright.sync_api import Page

from santander.config import DEFAULT_TIMEOUT_MS


def go_to_credit_card_movements(page: Page) -> None:
    page.locator("nav").get_by_text("Tarjetas", exact=True).first.click()
    page.get_by_text("Mis Tarjetas de Crédito", exact=True).wait_for(
        state="visible", timeout=DEFAULT_TIMEOUT_MS
    )
    page.get_by_text("Mis Tarjetas de Crédito", exact=True).click()

    page.wait_for_url("**/#/private/Saldos_TC/**", timeout=DEFAULT_TIMEOUT_MS)
    page.get_by_text("MOVIMIENTOS POR FACTURAR", exact=True).click()
    page.wait_for_url("**/#/private/Saldos_TC/main/bill**", timeout=DEFAULT_TIMEOUT_MS)
    page.locator("table").first.wait_for(state="visible", timeout=DEFAULT_TIMEOUT_MS)
