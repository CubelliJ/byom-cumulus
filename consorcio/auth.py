"""Consorcio login automation."""

from __future__ import annotations

import os
import re
import sys

from dotenv import load_dotenv
from playwright.sync_api import Page

from consorcio.config import DEFAULT_TIMEOUT_MS, HOME_URL


def load_credentials() -> tuple[str, str]:
    load_dotenv()
    rut = os.getenv("CONSORCIO_RUT", "").strip()
    password = os.getenv("CONSORCIO_PASSWORD", "").strip()
    if not rut or not password:
        print(
            "Missing Consorcio credentials. Set CONSORCIO_RUT and "
            "CONSORCIO_PASSWORD in .env",
            file=sys.stderr,
        )
        sys.exit(1)
    return rut, password


def _dismiss_banners(page: Page) -> None:
    for text in ("Entiendo", "Aceptar", "Cerrar"):
        locator = page.get_by_text(text, exact=True)
        if locator.count():
            try:
                locator.first.click(timeout=2000)
            except Exception:
                pass


def login(page: Page, rut: str | None = None, password: str | None = None) -> Page:
    if rut is None or password is None:
        rut, password = load_credentials()

    page.goto(HOME_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    page.wait_for_timeout(2000)
    _dismiss_banners(page)

    page.get_by_role("link", name=re.compile(r"Ir a Sucursal Virtual", re.I)).first.click()
    page.wait_for_timeout(3000)

    page.locator("#input-rut").press_sequentially(rut, delay=80)
    page.locator("#input-new-pass").press_sequentially(password, delay=80)
    page.get_by_role("button", name="Ingresar").click()

    page.wait_for_url("**personas.consorcio.cl**", timeout=DEFAULT_TIMEOUT_MS)
    page.wait_for_timeout(4000)
    return page
