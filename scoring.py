"""
Filtros de confiabilidad (requisito #2) y cálculo del score 0-100
(requisito #3): seguridad 40%, momentum de volumen/holders 30%, liquidez 30%.

También lleva un historial local (data/history.json) con el snapshot del
día anterior por token, para poder calcular "momentum" real de holders de
un día al siguiente (el bot corre una vez al día, así que comparar contra
la corrida anterior es la señal de momentum más honesta que se puede tener
sin pagar por una API con histórico).
"""

from __future__ import annotations

import json
import logging
import math
import time
from typing import Any

from config import (
    HISTORY_FILE,
    MAX_TOP10_HOLDER_PCT,
    MIN_AGE_HOURS,
    MIN_HOLDERS,
    MIN_LIQUIDITY_USD,
    MIN_LP_LOCKED_PCT,
    MIN_VOLUME_24H_USD,
)

logger = logging.getLogger(__name__)

LIQUIDITY_SCORE_FLOOR = MIN_LIQUIDITY_USD  # score 0 en el mínimo permitido
LIQUIDITY_SCORE_CEIL = 1_000_000  # score 100 a partir de $1M de liquidez


def load_history() -> dict[str, dict]:
    if not HISTORY_FILE.exists():
        return {}
    try:
        with open(HISTORY_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("No se pudo leer el historial (%s), se ignora", exc)
        return {}


def save_history(history: dict[str, dict]) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2)


def _age_hours(pair_created_at_ms: int | None) -> float | None:
    if not pair_created_at_ms:
        return None
    now_ms = time.time() * 1000
    return (now_ms - pair_created_at_ms) / 3_600_000


def cheap_prefilter(market_tokens: list[dict]) -> list[dict]:
    """Filtra usando solo datos de DexScreener (liquidez, volumen, edad),
    sin llamar a RugCheck todavía. Sirve para no gastar el rate limit de
    RugCheck (15 req/min) en tokens que de todas formas van a fallar."""
    result = []
    for token in market_tokens:
        age = _age_hours(token.get("pair_created_at_ms"))
        if (
            token["liquidity_usd"] >= MIN_LIQUIDITY_USD
            and token["volume_24h"] >= MIN_VOLUME_24H_USD
            and age is not None
            and age >= MIN_AGE_HOURS
        ):
            result.append(token)
    logger.info(
        "Preselección barata: %d/%d tokens pasan liquidez+volumen+edad (antes de RugCheck)",
        len(result),
        len(market_tokens),
    )
    return result


def check_filters(token: dict) -> list[str]:
    """Devuelve la lista de motivos por los que el token NO pasa los
    filtros de confiabilidad. Lista vacía = pasa todos los filtros."""
    reasons = []

    if token["liquidity_usd"] < MIN_LIQUIDITY_USD:
        reasons.append(f"liquidez ${token['liquidity_usd']:,.0f} < ${MIN_LIQUIDITY_USD:,.0f}")

    lp_locked = token.get("lp_locked_pct")
    if lp_locked is None or lp_locked < MIN_LP_LOCKED_PCT:
        shown = "desconocido" if lp_locked is None else f"{lp_locked:.1f}%"
        reasons.append(f"LP bloqueada/quemada {shown} < {MIN_LP_LOCKED_PCT:.0f}%")

    if not token.get("mint_authority_revoked"):
        reasons.append("mint authority NO revocada")
    if not token.get("freeze_authority_revoked"):
        reasons.append("freeze authority NO revocada")

    top10 = token.get("top10_holder_pct")
    if top10 is None or top10 > MAX_TOP10_HOLDER_PCT:
        shown = "desconocido" if top10 is None else f"{top10:.1f}%"
        reasons.append(f"top 10 holders {shown} > {MAX_TOP10_HOLDER_PCT:.0f}%")

    age = token.get("age_hours")
    if age is None or age < MIN_AGE_HOURS:
        shown = "desconocida" if age is None else f"{age:.1f}h"
        reasons.append(f"edad {shown} < {MIN_AGE_HOURS:.0f}h")

    holders = token.get("total_holders")
    if holders is None or holders < MIN_HOLDERS:
        shown = "desconocido" if holders is None else str(holders)
        reasons.append(f"holders {shown} < {MIN_HOLDERS}")

    if token["volume_24h"] < MIN_VOLUME_24H_USD:
        reasons.append(f"volumen 24h ${token['volume_24h']:,.0f} < ${MIN_VOLUME_24H_USD:,.0f}")

    if token.get("rugged"):
        reasons.append("marcado como 'rugged' por RugCheck")

    return reasons


def _liquidity_score(liquidity_usd: float) -> float:
    if liquidity_usd <= LIQUIDITY_SCORE_FLOOR:
        return 0.0
    if liquidity_usd >= LIQUIDITY_SCORE_CEIL:
        return 100.0
    span = math.log10(LIQUIDITY_SCORE_CEIL) - math.log10(LIQUIDITY_SCORE_FLOOR)
    pos = math.log10(liquidity_usd) - math.log10(LIQUIDITY_SCORE_FLOOR)
    return max(0.0, min(100.0, pos / span * 100))


def _volume_momentum_score(token: dict) -> float:
    volume_24h = token.get("volume_24h") or 0
    volume_1h = token.get("volume_1h") or 0
    if volume_24h <= 0:
        return 50.0
    run_rate_ratio = (volume_1h * 24) / volume_24h
    return max(0.0, min(100.0, run_rate_ratio * 50))


def _holders_momentum_score(token: dict, previous: dict | None) -> float:
    current = token.get("total_holders")
    if current is None:
        return 50.0
    if not previous or not previous.get("total_holders"):
        return 50.0  # sin dato previo, neutral
    prev_holders = previous["total_holders"]
    if prev_holders <= 0:
        return 50.0
    growth_pct = (current - prev_holders) / prev_holders * 100
    return max(0.0, min(100.0, 50 + growth_pct * 5))


def _security_score(token: dict) -> float:
    score = token.get("security_score")
    return 0.0 if score is None else max(0.0, min(100.0, score))


def score_token(token: dict, previous: dict | None) -> dict:
    security = _security_score(token)
    volume_mom = _volume_momentum_score(token)
    holders_mom = _holders_momentum_score(token, previous)
    momentum = (volume_mom + holders_mom) / 2
    liquidity = _liquidity_score(token["liquidity_usd"])

    final = round(0.4 * security + 0.3 * momentum + 0.3 * liquidity)

    return {
        **token,
        "score": max(0, min(100, final)),
        "score_breakdown": {
            "security": round(security, 1),
            "momentum": round(momentum, 1),
            "liquidity": round(liquidity, 1),
        },
    }


def evaluate_tokens(market_tokens: list[dict], security_by_address: dict[str, dict]) -> list[dict]:
    """Combina datos de mercado + seguridad, aplica filtros, calcula score
    y devuelve solo los tokens que pasan todos los filtros, ordenados por
    score descendente."""
    history = load_history()
    passed: list[dict] = []

    for market in market_tokens:
        address = market["address"]
        security = security_by_address.get(address)
        if security is None:
            logger.info("%s (%s): sin datos de seguridad, descartado", market.get("symbol"), address)
            continue

        token = {**market, **security, "age_hours": _age_hours(market.get("pair_created_at_ms"))}

        fail_reasons = check_filters(token)
        if fail_reasons:
            logger.info("%s (%s) descartado: %s", token.get("symbol"), address, "; ".join(fail_reasons))
            continue

        scored = score_token(token, history.get(address))
        passed.append(scored)

    passed.sort(key=lambda t: t["score"], reverse=True)

    # Actualiza el historial con el snapshot de hoy para todos los que pasaron filtros.
    new_history = load_history()
    for token in passed:
        new_history[token["address"]] = {
            "total_holders": token.get("total_holders"),
            "volume_24h": token.get("volume_24h"),
            "price_usd": token.get("price_usd"),
            "timestamp": time.time(),
        }
    save_history(new_history)

    logger.info("%d tokens pasaron todos los filtros de confiabilidad", len(passed))
    return passed


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from data_sources import dexscreener, rugcheck

    addrs = dexscreener.discover_candidate_addresses()
    market = dexscreener.get_market_data(addrs)
    preselected = cheap_prefilter(market)
    security = rugcheck.get_security_info_bulk([m["address"] for m in preselected])
    results = evaluate_tokens(preselected, security)

    for t in results[:10]:
        print(
            f"{t['score']:>3} {t['symbol']:<10} liq=${t['liquidity_usd']:,.0f} "
            f"holders={t['total_holders']} top10={t['top10_holder_pct']}% "
            f"sec={t['score_breakdown']['security']}"
        )
