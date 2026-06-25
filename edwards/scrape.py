"""Playwright helpers for Edwards movement tables."""

from __future__ import annotations

from playwright.sync_api import Page

from santander.scrape import EXTRACT_TABLE_ROWS_JS


def extract_movement_rows(page: Page) -> list[list[str]]:
    return page.evaluate(EXTRACT_TABLE_ROWS_JS)
