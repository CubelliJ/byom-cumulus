"""Banco Edwards / Banco de Chile web banking constants."""

LOGIN_URL = "https://login.portales.bancochile.cl/login"
PORTAL_BASE = (
    "https://portalpersonas.bancochile.cl/mibancochile-web/front/personaBEC/index.html"
)
CHECKING_MOVEMENTS_URL = PORTAL_BASE + "#/movimientos/cuenta/saldos-movimientos/"
CREDIT_CARD_MOVEMENTS_URL = PORTAL_BASE + "#/tarjeta-credito/consultar/saldos"

DEFAULT_TIMEOUT_MS = 60_000
