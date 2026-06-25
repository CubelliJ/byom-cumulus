"""Navigate Edwards portal to checking and credit card movements."""

from __future__ import annotations

from playwright.sync_api import Page

from edwards.auth import dismiss_modals
from edwards.config import (
    CHECKING_MOVEMENTS_URL,
    CREDIT_CARD_MOVEMENTS_URL,
    DEFAULT_TIMEOUT_MS,
)


def go_to_checking_movements(page: Page) -> None:
    page.goto(CHECKING_MOVEMENTS_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    page.wait_for_timeout(3000)
    dismiss_modals(page)
    page.locator("table").first.wait_for(state="visible", timeout=DEFAULT_TIMEOUT_MS)


def go_to_credit_card_movements(page: Page) -> None:
    page.goto(
        CREDIT_CARD_MOVEMENTS_URL,
        wait_until="domcontentloaded",
        timeout=DEFAULT_TIMEOUT_MS,
    )
    page.wait_for_timeout(3000)
    dismiss_modals(page)
    page.locator("table").first.wait_for(state="visible", timeout=DEFAULT_TIMEOUT_MS)
