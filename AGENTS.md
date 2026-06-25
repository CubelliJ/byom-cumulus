# Agent guide — byom-finsonal

This repo implements **Bring Your Own Movements** for [cumulus](https://trycumulus.com): local Playwright scrapers per Chilean bank, a shared push client, and a consistent “today only → preview → cumulus” flow.

Read this before adding a bank, fixing a broken scraper, or refactoring shared code.

## Architecture

Each bank is a small Python package plus a top-level `sync_<bank>.py` orchestrator.

```
sync_<bank>.py          # CLI, browser lifecycle, preview, push
<bank>/
  config.py             # URLs, timeouts
  auth.py               # login from public entry page
  navigate.py           # post-login routes to movement pages
  scrape.py             # DOM → raw rows (list[list[str]])
  parse.py              # raw rows → cumulus movement dicts
push.py                 # cumulus API (shared)
santander/browser.py    # shared Playwright launch + debug screenshots
santander/parse.py      # shared CLP/date parsing (reused by Consorcio)
```

**Orchestrator pattern** (every `sync_*.py` should follow this):

1. Launch headed Chromium (banks often block headless).
2. `login(page)` — credentials from `.env`, return authenticated `page`.
3. Navigate → `extract_movement_rows(page)` → `parse_*_rows(...)`.
4. Filter to **today** in `America/Santiago`.
5. `preview_movements()` in terminal.
6. Unless `--dry-run`: `push(movements)` via `push.py`.
7. On failure: `save_debug_screenshot(page)` → `debug/last-failure.png`.

Keep bank-specific logic in `<bank>/`. Do not put Santander selectors in Consorcio files.

## cumulus contract

Only `POST /imports/push` is used. Token from `CUMULUS_API_KEY` or `CUMULUS_TOKEN`.

Required per movement:

| Field | Type | Notes |
|-------|------|-------|
| `date` | `YYYY-MM-DD` | ISO date |
| `merchant` | string | Payee/description; used for dedup |
| `amount` | int | Positive CLP |
| `is_credit` | bool, optional | `true` for abonos/income |

Do **not** send `paid_by_member_id` — the server assigns the token holder.

Classification hints (`bucket_type`, `category`) are intentionally omitted in v1; review happens in cumulus.

Dedup on server: same `date` + `amount` + `merchant` → `push_skipped_duplicates`.

## Methodology for adding or fixing a bank

### 1. Explore before coding

Use a throwaway script or `playwright` REPL with **headed** browser and real credentials from `.env`:

1. Start at the bank’s **public entry URL** (not deep links unless login session exists).
2. Record login selectors (`#rut`, `#pass`, submit button quirks).
3. After login, find the **movement list** for the target account type.
4. Dump `page.url`, `body.innerText`, table/`cns-table` structure, and 3–5 sample rows.
5. Save `debug/*.png` when stuck.

**Do not guess selectors.** Chilean bank UIs are Angular/Vue SPAs with overlays, iframes, and duplicate element IDs.

### 2. Auth patterns we’ve learned

| Bank | Entry | Login quirks |
|------|-------|--------------|
| Santander | `banco.santander.cl/personas` → Ingresar iframe | `#rut`, `#pass`, INGRESAR; wait for `mibanco.santander.cl` + `¡Hola,` |
| Consorcio | `sitio.consorcio.cl/home` → Sucursal Virtual | `#input-rut`, `#input-new-pass`; use `press_sequentially` (not `fill`) so RUT mask enables `#btn-login` |

Dismiss cookie/banner modals (`Entiendo`, `Aceptar`) before clicking.

Credentials: `BANK_RUT` + `BANK_PASSWORD` in `.env`. Never hardcode or log them.

### 3. Navigation patterns

Prefer **direct post-login URLs** when the SPA hash route is stable:

- Santander checking: `#/private/saldos/main/movimientos`
- Santander TC (unbilled): `#/private/Saldos_TC/main/bill`
- Consorcio checking: `personas.consorcio.cl/.../ultimos-movimientos`

Use menu clicking only when URLs are unstable. If a side menu stays open and intercepts clicks, navigate by URL instead of fighting overlays.

### 4. Scraping

Return `list[list[str]]` — one inner list per movement, cells as displayed.

Implementations:

- **HTML tables** (`<table>`) — Santander; use generic row extraction in `santander/scrape.py`.
- **Web components** (`<cns-table>`) — Consorcio; flat div walk, chunk every 6 cells per row.

Scraper should not parse dates or amounts; that belongs in `parse.py`.

### 5. Parsing (shared rules in `santander/parse.py`)

- **Today filter:** `today_chile()` using `ZoneInfo("America/Santiago")`.
- **Dates:** `DD/MM/YYYY`, `DD/MM/YY`, or `DD/MM` (year inferred from today).
- **Amounts:** only cells containing `$`; CLP with `.` thousands separators.
- **Signed amounts:** `-` prefix → expense; `+` or abono column → `is_credit: true`.
- **Skip rows** matching `SKIP_MERCHANT_RE`: card payments, saldo inicial, traspaso a tarjeta de crédito (avoids double-count with TC sync).

Santander TC rows may omit date on continuation lines — `normalize_santander_rows()` carries the date forward.

Consorcio reuses `row_to_movement()` via `[date, merchant, amount_cell]` slicing.

### 6. CLI conventions

Every `sync_*.py` exposes the same flags:

- `--dry-run` — no API call
- `--confirm` — `y/N` before push
- `--inspect` — page text dump
- `--headless` — optional; default is headed

Default behavior: auto-push (cumulus dedupes). Use `--confirm` while tuning a new scraper.

### 7. Testing a change

1. `python sync_<bank>.py --dry-run` — verify today’s rows look correct.
2. `python sync_<bank>.py --confirm` — push once, check cumulus review UI.
3. Re-run dry-run — expect `push_skipped_duplicates` on second push.

Quick parser unit tests can live inline or in a small script; no test suite required for trivial changes.

### 8. What not to do

- Do not commit `.env`, tokens, or `debug/` screenshots with account data.
- Do not use `networkidle` on bank SPAs — it hangs; use `domcontentloaded` + visible selectors.
- Do not send classification hints until parsing is rock-solid.
- Do not add headless-only flows without verifying the bank allows it.
- Do not expand scope in `push.py` beyond the BYOM API surface.

## Current bank details

### Santander (`sync_santander.py`)

- Logs in via personas iframe → `mibanco.santander.cl`.
- Scrapes **both** checking and credit card in one session.
- Merges with `merge_movements()`; dedupes locally before push.
- TC path: movimientos por facturar (unbilled).

### Consorcio (`sync_consorcio.py`)

- No credit card on this account — **checking only**.
- Path: home → Sucursal Virtual → Saldos y Movimientos.
- Parses `<cns-table>` rows (6 cells: date, merchant, ref, amount ×2, balance).

## Adding the next bank

1. Copy the `consorcio/` layout to `<newbank>/`.
2. Add `sync_<newbank>.py` mirroring existing orchestrators.
3. Document entry URL and env vars (`NEWBANK_RUT`, `NEWBANK_PASSWORD`) in README.
4. Explore login + movements page with headed Playwright first.
5. Ship with `--dry-run` only; enable default push after manual validation in cumulus review.

## Useful references

- [cumulus BYOM blog post](https://trycumulus.com/blog/bring-your-own-movements)
- cumulus API base: `https://api.trycumulus.com`
- Playwright Python: headed Chromium, `press_sequentially` for masked inputs, `page.evaluate` for table extraction
