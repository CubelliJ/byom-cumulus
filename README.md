# byom-cumulus

Bring Your Own Movements (BYOM) clients that scrape today's bank transactions locally and push them to [cumulus](https://trycumulus.com) for review and import.

Credentials stay on your machine. cumulus only receives movement rows you push via the Automation API.

## Supported banks

| Bank | Script | Accounts | Entry URL |
|------|--------|----------|-----------|
| Santander Chile | `sync_santander.py` | Cuenta corriente + tarjeta de crédito | [banco.santander.cl/personas](https://banco.santander.cl/personas) |
| Banco Edwards | `sync_edwards.py` | Cuenta corriente + tarjeta de crédito | [login.portales.bancochile.cl/login](https://login.portales.bancochile.cl/login) |
| Banco Consorcio | `sync_consorcio.py` | Cuenta corriente (Cuenta Más) | [sitio.consorcio.cl/home](https://sitio.consorcio.cl/home) |

Each sync filters to **today's movements** in `America/Santiago`, then POSTs to cumulus. Deduping happens on the server (date + amount + merchant).

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Create `.env` in the project root (never commit it):

```bash
# cumulus — generate in Settings → Automation API
CUMULUS_API_KEY=cmr_...

# Santander
SANTANDER_RUT=12345678-9
SANTANDER_PASSWORD=...

# Edwards (Banco de Chile portal)
EDWARDS_RUT=12345678-9
EDWARDS_PASSWORD=...

# Consorcio
CONSORCIO_RUT=12345678-9
CONSORCIO_PASSWORD=...
```

`CUMULUS_TOKEN` also works instead of `CUMULUS_API_KEY`.

## Usage

### Santander (checking + credit card)

```bash
.venv/bin/python sync_santander.py --dry-run    # preview only
.venv/bin/python sync_santander.py --confirm  # ask before push
.venv/bin/python sync_santander.py            # auto-push
```

### Banco Edwards (checking + credit card)

```bash
.venv/bin/python sync_edwards.py --dry-run
.venv/bin/python sync_edwards.py --confirm
.venv/bin/python sync_edwards.py
```

### Consorcio (checking)

```bash
.venv/bin/python sync_consorcio.py --dry-run
.venv/bin/python sync_consorcio.py --confirm
.venv/bin/python sync_consorcio.py
```

### All banks

```bash
.venv/bin/python sync_all.py              # Santander → Edwards → Consorcio, auto-push
.venv/bin/python sync_all.py --dry-run    # preview all, no push
```

cumulus dedupes on every push (`date` + `amount` + `merchant`), so re-running every few hours only appends new movements. Repeats show up as `skipped duplicates` in the output.

### Manual push (no browser)

```bash
.venv/bin/python push.py --date 2026-06-24 --merchant "Coffee" --amount 3500
.venv/bin/python push.py --file movements.json
```

### Flags (all sync scripts)

| Flag | Effect |
|------|--------|
| `--dry-run` | Scrape and print preview; never call cumulus |
| `--confirm` | Prompt `y/N` before pushing |
| `--inspect` | Dump page text after navigation (debug) |
| `--headless` | Headless browser (often blocked by banks) |

## After you push

1. Open cumulus → **Review imports**
2. Check classification, payer, and bucket per row
3. Import selected rows

Rows outside your household period may show as **Out of period** but still appear in the queue.

## Project layout

```
push.py                 # cumulus API client + CLI
sync_santander.py       # Santander orchestration
sync_edwards.py         # Banco Edwards orchestration
sync_consorcio.py       # Consorcio orchestration
sync_all.py             # all banks in sequence
santander/              # auth, navigate, scrape, parse
edwards/                # auth, navigate, scrape, parse
consorcio/              # auth, navigate, scrape, parse
```

## cumulus API

- **Endpoint:** `POST https://api.trycumulus.com/imports/push`
- **Auth:** `Authorization: Bearer <token>`
- **Docs:** [Bring Your Own Movements](https://trycumulus.com/blog/bring-your-own-movements)

Movement payload (minimal):

```json
{
  "movements": [
    {
      "date": "2026-06-24",
      "merchant": "Lider Express",
      "amount": 12500,
      "is_credit": false
    }
  ]
}
```

`amount` is a positive integer in CLP. Set `is_credit: true` for income/abonos.

## Scheduling (optional)

Runs every **4 hours** at 00:00, 04:00, 08:00, 12:00, 16:00, and 20:00 **Chile time** (`America/Santiago`). cumulus dedupes repeats, so only new movements are appended.

**macOS (launchd):**

```bash
chmod +x scripts/install_launchd.sh scripts/run_sync_all.sh
./scripts/install_launchd.sh
```

Logs go to `logs/sync-YYYY-MM-DD.log`. Uninstall:

```bash
launchctl bootout gui/$(id -u)/com.byom-cumulus.sync
rm ~/Library/LaunchAgents/com.byom-cumulus.sync.plist
```

**Manual one-off (or cron):**

```bash
./scripts/run_sync_all.sh
```

Cron example (every 4 hours, Chile TZ):

```bash
0 0,4,8,12,16,20 * * * TZ=America/Santiago cd /path/to/byom-cumulus && ./scripts/run_sync_all.sh
```

Requires a logged-in Mac session — Playwright runs headed Chromium and banks often block headless automation.


## Security

- Do not commit `.env` or tokens
- Bank passwords live only in `.env` on your machine
- Regenerate the cumulus token if it may have leaked
