"""
Fuente de datos de respaldo: RPC público de Solana.

La API pública de Solscan (public-api.solscan.io) fue descontinuada: hoy
devuelve 404 y Solscan exige API key de pago (pro-api.solscan.io) para casi
todo. Por eso, como respaldo cuando RugCheck no tiene reporte de un token
(404, token no indexado todavía), usamos directamente el RPC público de
Solana (https://api.mainnet-beta.solana.com), que no requiere API key.

Limitación importante: el RPC público limita fuertemente los métodos caros
como getTokenLargestAccounts (se ve 429 "Too many requests" con frecuencia).
Por eso este módulo reintenta con backoff, y si no logra respuesta se
devuelve top10_holder_pct=None en vez de inventar un dato. Además, el RPC
NO permite obtener el número total de holders de un token sin un indexador
(requeriría getProgramAccounts, deshabilitado/limitado en nodos públicos),
así que total_holders siempre queda como None en este módulo: el bot trata
esto como "dato insuficiente" y descarta el token en vez de asumir que pasa
el filtro de holders mínimos.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from config import HTTP_TIMEOUT

logger = logging.getLogger(__name__)

RPC_URL = "https://api.mainnet-beta.solana.com"
TOKEN_PROGRAM_2022 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
MAX_RETRIES = 3


def _rpc_call(method: str, params: list) -> Any | None:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(RPC_URL, json=payload, timeout=HTTP_TIMEOUT)
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("RPC: fallo de red en %s (intento %d): %s", method, attempt, exc)
            time.sleep(2 * attempt)
            continue

        error = data.get("error")
        if error:
            if error.get("code") == 429:
                wait = 3 * attempt
                logger.info("RPC: rate limited en %s, esperando %ds", method, wait)
                time.sleep(wait)
                continue
            logger.warning("RPC: error en %s: %s", method, error)
            return None
        return data.get("result")
    return None


def get_mint_authorities(mint: str) -> dict | None:
    """Devuelve {'mint_authority_revoked': bool, 'freeze_authority_revoked': bool}
    consultando la cuenta del mint vía getAccountInfo(jsonParsed)."""
    result = _rpc_call("getAccountInfo", [mint, {"encoding": "jsonParsed"}])
    if not result or not result.get("value"):
        return None
    try:
        info = result["value"]["data"]["parsed"]["info"]
    except (KeyError, TypeError):
        return None
    return {
        "mint_authority_revoked": info.get("mintAuthority") is None,
        "freeze_authority_revoked": info.get("freezeAuthority") is None,
    }


def get_top10_holder_pct(mint: str) -> float | None:
    """Calcula el % del supply en manos de los 10 mayores holders (cuentas
    de token, sin resolver 'owner' ni excluir pools -- es una aproximación
    de respaldo, menos precisa que la de RugCheck)."""
    largest = _rpc_call("getTokenLargestAccounts", [mint])
    supply = _rpc_call("getTokenSupply", [mint])
    if largest is None or supply is None:
        return None
    try:
        total = float(supply["value"]["uiAmount"] or 0)
        if total <= 0:
            return None
        top10_amount = sum(float(a["uiAmount"] or 0) for a in largest["value"][:10])
        return round(top10_amount / total * 100, 2)
    except (KeyError, TypeError, ZeroDivisionError):
        return None


def get_security_info_fallback(mint: str) -> dict | None:
    """Intenta reconstruir la info mínima de seguridad usando solo RPC.
    total_holders queda como None (no se puede obtener sin indexador)."""
    authorities = get_mint_authorities(mint)
    if authorities is None:
        return None
    top10_pct = get_top10_holder_pct(mint)

    return {
        "address": mint,
        "mint_authority_revoked": authorities["mint_authority_revoked"],
        "freeze_authority_revoked": authorities["freeze_authority_revoked"],
        "total_holders": None,  # no disponible vía RPC público
        "top10_holder_pct": top10_pct,
        "lp_locked_pct": None,  # no disponible vía RPC público
        "security_score": None,  # no hay score de riesgo sin RugCheck
        "rugged": False,
        "risks": [],
        "source": "solana_rpc_fallback",
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    mint = "FRS2TzZZGv4X4kx9a2wiMWyrTBRN9CYDRmp9quUTpump"
    print("Authorities:", get_mint_authorities(mint))
    print("Top10 pct:", get_top10_holder_pct(mint))
    print("Fallback completo:", get_security_info_fallback(mint))
