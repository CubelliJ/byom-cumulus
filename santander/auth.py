"""Santander login automation."""

from __future__ import annotations

import os
import re
import sys

from dotenv import load_dotenv
from playwright.sync_api import Page

from santander.config import DEFAULT_TIMEOUT_MS, PERSONAS_URL


def load_credentials() -> tuple[str, str]:
    load_dotenv()
    rut = os.getenv("SANTANDER_RUT", "").strip()
    password = os.getenv("SANTANDER_PASSWORD", "").strip()
    if not rut or not password:
        print(
            "Missing Santander credentials. Set SANTANDER_RUT and "
            "SANTANDER_PASSWORD in .env",
            file=sys.stderr,
        )
        sys.exit(1)
    return rut, password


def login(page: Page, rut: str | None = None, password: str | None = None) -> Page:
    if rut is None or password is None:
        rut, password = load_credentials()

    page.goto(PERSONAS_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    page.locator("#btnIngresar").click()

    login_frame = page.frame_locator('iframe[src*="mibanco.santander.cl"]')
    login_frame.locator("#rut").wait_for(state="visible", timeout=DEFAULT_TIMEOUT_MS)
    login_frame.locator("#rut").fill(rut)
    login_frame.locator("#pass").fill(password)
    login_frame.get_by_role("button", name="Ingresar").click()

    page.wait_for_url("**mibanco.santander.cl**", timeout=DEFAULT_TIMEOUT_MS)
    page.wait_for_load_state("domcontentloaded")
    page.get_by_text(re.compile(r"¡Hola,", re.IGNORECASE)).wait_for(
        timeout=DEFAULT_TIMEOUT_MS
    )
    return page
