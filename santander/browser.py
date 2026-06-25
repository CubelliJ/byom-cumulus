"""Browser setup for Santander automation."""

from __future__ import annotations

from playwright.sync_api import Browser, BrowserContext, Playwright


def launch_browser(playwright: Playwright, *, headless: bool) -> tuple[Browser, BrowserContext]:
    browser = playwright.chromium.launch(
        headless=headless,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        locale="es-CL",
        viewport={"width": 1280, "height": 900},
    )
    return browser, context


def save_debug_screenshot(page, path: str = "debug/last-failure.png") -> None:
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(target), full_page=True)
