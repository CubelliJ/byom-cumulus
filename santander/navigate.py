"""Navigate Santander private site to account and card movements."""

from __future__ import annotations

from playwright.sync_api import Page

from santander.config import DEFAULT_TIMEOUT_MS

CHECKING_MOVEMENTS_URL = (
    "https://mibanco.santander.cl/UI.Web.HB/Private_new/frame/"
    "#/private/saldos/main/movimientos"
)
CREDIT_CARD_MOVEMENTS_URL = (
    "https://mibanco.santander.cl/UI.Web.HB/Private_new/frame/"
    "#/private/Saldos_TC/main/bill"
)


def go_to_checking_movements(page: Page) -> None:
    page.goto(CHECKING_MOVEMENTS_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    page.wait_for_timeout(2000)
    page.locator("table").first.wait_for(state="visible", timeout=DEFAULT_TIMEOUT_MS)


def go_to_credit_card_movements(page: Page) -> None:
    page.goto(CREDIT_CARD_MOVEMENTS_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    page.wait_for_timeout(2000)
    page.locator("table").first.wait_for(state="visible", timeout=DEFAULT_TIMEOUT_MS)
