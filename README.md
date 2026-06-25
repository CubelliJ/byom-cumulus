# byom-finsonal

Bring Your Own Movements (BYOM) clients that scrape today's bank transactions locally and push them to [cumulus](https://trycumulus.com) for review and import.

Credentials stay on your machine. cumulus only receives movement rows you push via the Automation API.

## Supported banks

| Bank | Script | Accounts | Entry URL |
|------|--------|----------|-----------|
| Santander Chile | `sync_santander.py` | Cuenta corriente + tarjeta de crédito | [banco.santander.cl/personas](https://banco.santander.cl/personas) |
| Banco Consorcio | `sync_consorcio.py` | Cuenta corriente (Cuenta Más) | [sitio.consorcio.cl/home](https://sitio.consorcio.cl/home) |

Each sync filters to **today's movements** in `America/Santiago`, then POSTs to cumulus. Deduping happens on the server (date + amount + merchant).

## Setup

```bash
python3 -m venv .venv
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

### Consorcio (checking)

```bash
.venv/bin/python sync_consorcio.py --dry-run
.venv/bin/python sync_consorcio.py --confirm
.venv/bin/python sync_consorcio.py
```

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
sync_consorcio.py       # Consorcio orchestration
santander/              # auth, navigate, scrape, parse
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

```bash
# example: daily at 9pm Chile time
0 21 * * * cd /path/to/byom-finsonal && .venv/bin/python sync_santander.py
0 21 * * * cd /path/to/byom-finsonal && .venv/bin/python sync_consorcio.py
```

## Security

- Do not commit `.env` or tokens
- Bank passwords live only in `.env` on your machine
- Regenerate the cumulus token if it may have leaked
