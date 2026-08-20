"""
Fuente de datos: DexScreener (https://docs.dexscreener.com/api/reference)

DexScreener no ofrece un endpoint público que liste "todos los pares nuevos
de Solana". Como alternativa (gratis, sin API key) combinamos dos endpoints
que sí existen para descubrir tokens en circulación / con actividad reciente:

  - /token-profiles/latest/v1  -> tokens que cargaron un perfil recientemente
  - /token-boosts/latest/v1    -> tokens recién "boosteados"
  - /token-boosts/top/v1       -> tokens con más boosts activos

y luego pedimos los datos de mercado (precio, liquidez, volumen, etc.) de
cada token con /tokens/v1/{chainId}/{addresses} (hasta 30 direcciones por
llamada).

Un token puede tener varios pares (varios DEX). Nos quedamos con el par de
mayor liquidez como "par principal".
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from config import CHAIN_ID, HTTP_TIMEOUT

logger = logging.getLogger(__name__)

BASE_URL = "https://api.dexscreener.com"
CANDIDATE_ENDPOINTS = [
    "/token-profiles/latest/v1",
    "/token-boosts/latest/v1",
    "/token-boosts/top/v1",
]
BATCH_SIZE = 30


def _get(url: str, params: dict | None = None) -> Any:
    resp = requests.get(url, params=params, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def discover_candidate_addresses(chain_id: str = CHAIN_ID) -> list[str]:
    """Descubre direcciones de tokens candidatos combinando varios endpoints
    de descubrimiento de DexScreener. Devuelve direcciones únicas."""
    addresses: dict[str, None] = {}  # dict para preservar orden y deduplicar
    for endpoint in CANDIDATE_ENDPOINTS:
        try:
            data = _get(BASE_URL + endpoint)
        except requests.RequestException as exc:
            logger.warning("Fallo al consultar %s: %s", endpoint, exc)
            continue
        if not isinstance(data, list):
            continue
        for item in data:
            if item.get("chainId") == chain_id and item.get("tokenAddress"):
                addresses[item["tokenAddress"]] = None
    logger.info("Descubiertos %d tokens candidatos en %s", len(addresses), chain_id)
    return list(addresses.keys())


def _chunk(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _pick_main_pair(pairs: list[dict]) -> dict | None:
    """De todos los pares de un mismo token, elige el de mayor liquidez USD."""
    best = None
    best_liq = -1.0
    for pair in pairs:
        liq = (pair.get("liquidity") or {}).get("usd") or 0
        if liq > best_liq:
            best_liq = liq
            best = pair
    return best


def _normalize_pair(pair: dict) -> dict:
    base = pair.get("baseToken", {})
    liquidity = pair.get("liquidity", {}) or {}
    volume = pair.get("volume", {}) or {}
    price_change = pair.get("priceChange", {}) or {}
    txns = pair.get("txns", {}) or {}

    return {
        "address": base.get("address"),
        "name": base.get("name"),
        "symbol": base.get("symbol"),
        "price_usd": float(pair.get("priceUsd") or 0),
        "market_cap": pair.get("marketCap") or pair.get("fdv") or 0,
        "liquidity_usd": float(liquidity.get("usd") or 0),
        "volume_24h": float(volume.get("h24") or 0),
        "volume_1h": float(volume.get("h1") or 0),
        "price_change_24h": float(price_change.get("h24") or 0),
        "txns_h24": txns.get("h24", {}),
        "pair_created_at_ms": pair.get("pairCreatedAt"),
        "dex_id": pair.get("dexId"),
        "pair_address": pair.get("pairAddress"),
        "url": pair.get("url"),
    }


def get_market_data(addresses: list[str], chain_id: str = CHAIN_ID) -> list[dict]:
    """Dada una lista de direcciones de token, devuelve datos de mercado
    normalizados (uno por token, usando el par de mayor liquidez)."""
    results: dict[str, dict] = {}
    for batch in _chunk(addresses, BATCH_SIZE):
        joined = ",".join(batch)
        url = f"{BASE_URL}/tokens/v1/{chain_id}/{joined}"
        try:
            pairs = _get(url)
        except requests.RequestException as exc:
            logger.warning("Fallo al pedir datos de mercado para %d tokens: %s", len(batch), exc)
            continue
        if not isinstance(pairs, list):
            continue

        by_token: dict[str, list[dict]] = {}
        for pair in pairs:
            addr = (pair.get("baseToken") or {}).get("address")
            if addr:
                by_token.setdefault(addr, []).append(pair)

        for addr, token_pairs in by_token.items():
            main_pair = _pick_main_pair(token_pairs)
            if main_pair:
                results[addr] = _normalize_pair(main_pair)

        time.sleep(0.3)  # cortesía, evitar ráfagas

    logger.info("Datos de mercado obtenidos para %d/%d tokens", len(results), len(addresses))
    return list(results.values())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    addrs = discover_candidate_addresses()
    print(f"Candidatos encontrados: {len(addrs)}")
    print(addrs[:10])

    market = get_market_data(addrs[:10])
    for m in market:
        print(
            f"{m['symbol']:<12} liq=${m['liquidity_usd']:,.0f} "
            f"vol24h=${m['volume_24h']:,.0f} chg24h={m['price_change_24h']}% "
            f"mc=${m['market_cap']:,.0f}"
        )
