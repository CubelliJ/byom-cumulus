"""Banco Edwards login automation."""

from __future__ import annotations

import os
import re
import sys

from dotenv import load_dotenv
from playwright.sync_api import Page

from edwards.config import DEFAULT_TIMEOUT_MS, LOGIN_URL


def load_credentials() -> tuple[str, str]:
    load_dotenv()
    rut = os.getenv("EDWARDS_RUT", "").strip()
    password = os.getenv("EDWARDS_PASSWORD", "").strip()
    if not rut or not password:
        print(
            "Missing Edwards credentials. Set EDWARDS_RUT and "
            "EDWARDS_PASSWORD in .env",
            file=sys.stderr,
        )
        sys.exit(1)
    return rut, password


def dismiss_modals(page: Page) -> None:
    page.keyboard.press("Escape")
    page.evaluate("() => document.getElementById('modal_emergente_close')?.click()")
    page.wait_for_timeout(400)


def login(page: Page, rut: str | None = None, password: str | None = None) -> Page:
    if rut is None or password is None:
        rut, password = load_credentials()

    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    page.wait_for_timeout(2000)

    page.get_by_placeholder(re.compile(r"rut", re.I)).first.press_sequentially(
        rut, delay=80
    )
    page.locator("input[type='password']").first.press_sequentially(password, delay=80)
    page.get_by_role("button", name=re.compile(r"ingresar", re.I)).first.click()

    page.wait_for_url("**portalpersonas.bancochile.cl**", timeout=DEFAULT_TIMEOUT_MS)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(4000)
    dismiss_modals(page)
    return page
