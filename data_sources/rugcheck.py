"""
Fuente de datos: RugCheck (https://api.rugcheck.xyz)

Endpoint público, sin API key: GET /v1/tokens/{mint}/report

De ahí sacamos:
  - mint_authority / freeze_authority revocadas
  - concentración del top 10 de holders (excluyendo las cuentas de los
    propios pools de liquidez, que no son "ballenas" sino la liquidez
    del propio par)
  - número total de holders
  - % de liquidez bloqueada/quemada (lpLockedPct del pool principal)
  - score de riesgo propio de RugCheck (score_normalised: 0 = seguro,
    100 = muy riesgoso -> lo invertimos a "seguridad" 0-100)
  - banderas rojas (campo "risks")
  - flag "rugged" (ya fue detectado como rug)

RugCheck limita a ~15 requests/min (visto en el header
X-Rate-Limit-Limit), así que espaciamos las llamadas.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from config import HTTP_TIMEOUT, RUGCHECK_MAX_REQUESTS_PER_MINUTE

logger = logging.getLogger(__name__)

BASE_URL = "https://api.rugcheck.xyz/v1"
MIN_SECONDS_BETWEEN_REQUESTS = 60 / RUGCHECK_MAX_REQUESTS_PER_MINUTE


def _get_report(mint: str) -> dict | None:
    url = f"{BASE_URL}/tokens/{mint}/report"
    try:
        resp = requests.get(url, timeout=HTTP_TIMEOUT)
    except requests.RequestException as exc:
        logger.warning("RugCheck: fallo de red para %s: %s", mint, exc)
        return None

    if resp.status_code == 404:
        logger.info("RugCheck: sin reporte para %s (token no indexado)", mint)
        return None
    if resp.status_code == 429:
        logger.warning("RugCheck: rate limit alcanzado, esperando 60s")
        time.sleep(60)
        return _get_report(mint)
    try:
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("RugCheck: error HTTP para %s: %s", mint, exc)
        return None

    return resp.json()


def _pool_related_addresses(report: dict) -> set[str]:
    """Direcciones que pertenecen a los pools de liquidez (no son holders
    reales, así que se excluyen del cálculo de concentración)."""
    addrs: set[str] = set()
    for market in report.get("markets") or []:
        for key in ("pubkey", "liquidityA", "liquidityB", "mintLP"):
            val = market.get(key)
            if val:
                addrs.add(val)
    return addrs


def _top10_holder_pct(report: dict) -> float:
    pool_addrs = _pool_related_addresses(report)
    real_holders = [
        h
        for h in (report.get("topHolders") or [])
        if h.get("address") not in pool_addrs and h.get("owner") not in pool_addrs
    ]
    real_holders.sort(key=lambda h: h.get("pct", 0), reverse=True)
    return sum(h.get("pct", 0) for h in real_holders[:10])


def _lp_locked_pct(report: dict) -> float:
    markets = report.get("markets") or []
    if not markets:
        return 0.0
    # Tomamos el mercado con más liquidez como el pool principal.
    main_market = max(
        markets,
        key=lambda m: (m.get("lp") or {}).get("lpLockedUSD", 0) or 0,
    )
    return float((main_market.get("lp") or {}).get("lpLockedPct", 0) or 0)


def get_security_info(mint: str) -> dict | None:
    """Devuelve un dict normalizado con la información de seguridad del
    token, o None si RugCheck no tiene datos para ese mint."""
    report = _get_report(mint)
    if report is None:
        return None

    score_normalised = report.get("score_normalised", 100)  # 0 seguro, 100 riesgoso
    risks = [
        {
            "name": r.get("name"),
            "level": r.get("level"),
            "description": r.get("description"),
        }
        for r in (report.get("risks") or [])
    ]

    return {
        "address": report.get("mint"),
        "mint_authority_revoked": report.get("mintAuthority") is None,
        "freeze_authority_revoked": report.get("freezeAuthority") is None,
        "total_holders": report.get("totalHolders", 0),
        "top10_holder_pct": round(_top10_holder_pct(report), 2),
        "lp_locked_pct": round(_lp_locked_pct(report), 2),
        "security_score": round(100 - score_normalised, 2),  # invertido: 100 = muy seguro
        "rugged": bool(report.get("rugged", False)),
        "risks": risks,
    }


def get_security_info_bulk(mints: list[str]) -> dict[str, dict]:
    """Pide el reporte de seguridad de varios mints, respetando el rate
    limit de RugCheck. Devuelve {address: security_info} solo para los
    que tuvieron reporte disponible."""
    results: dict[str, dict] = {}
    for i, mint in enumerate(mints):
        info = get_security_info(mint)
        if info:
            results[mint] = info
        if i < len(mints) - 1:
            time.sleep(MIN_SECONDS_BETWEEN_REQUESTS)
    logger.info("RugCheck: seguridad obtenida para %d/%d tokens", len(results), len(mints))
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    test_mints = [
        "FRS2TzZZGv4X4kx9a2wiMWyrTBRN9CYDRmp9quUTpump",  # token nuevo, LP bloqueada
        "CrThUZJfQdjtNNzXAg6uo1ts7Nojgb6LakSvpviLpump",  # creador con historial de rugs
        "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",  # WIF, token establecido
    ]
    for m in test_mints:
        info = get_security_info(m)
        print(m, "->", info)
        time.sleep(MIN_SECONDS_BETWEEN_REQUESTS)
