"""Shared Playwright browser setup for all bank syncs."""

from __future__ import annotations

from typing import Literal

from playwright.sync_api import Browser, BrowserContext, Playwright

BrowserMode = Literal["unattended", "headfull", "headless"]

_STEALTH_ARGS = ["--disable-blink-features=AutomationControlled"]
_OFFSCREEN_ARGS = [
    *_STEALTH_ARGS,
    "--window-position=-32000,-32000",
    "--window-size=1280,900",
]


def launch_browser(
    playwright: Playwright,
    *,
    mode: BrowserMode = "unattended",
) -> tuple[Browser, BrowserContext]:
    """Launch Chromium for bank scraping.

    unattended (default): headed Chromium positioned off-screen. Banks often block
    true headless; this runs without a visible window on your display.
    headfull: visible browser window (debugging / selector tuning).
    headless: Playwright headless (may be blocked; useful on Linux servers).
    """
    if mode == "headless":
        browser = playwright.chromium.launch(headless=True, args=_STEALTH_ARGS)
    else:
        args = _STEALTH_ARGS if mode == "headfull" else _OFFSCREEN_ARGS
        browser = playwright.chromium.launch(headless=False, args=args)

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


def add_browser_args(parser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--headfull",
        action="store_true",
        help="Show the browser window for debugging (default: off-screen)",
    )
    group.add_argument(
        "--headless",
        action="store_true",
        help="True headless Chromium (often blocked by banks)",
    )


def browser_mode_from_args(args) -> BrowserMode:
    if args.headless:
        return "headless"
    if args.headfull:
        return "headfull"
    return "unattended"


def save_debug_screenshot(page, path: str = "debug/last-failure.png") -> None:
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(target), full_page=True)
