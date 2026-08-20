"""
Fuente de datos adicional para AMPLIAR el descubrimiento de tokens:
Jupiter Token API v2 (https://dev.jup.ag/docs/token-api/v2), pública y sin
API key.

DexScreener por sí solo (ver dexscreener.py) solo expone ~50-60 tokens
candidatos por corrida (los que tienen perfil o boost activo). Jupiter da
tres listados adicionales, gratis, que amplían bastante ese universo:

  - /tokens/v2/recent              -> últimos ~30 tokens creados
  - /tokens/v2/toptrending/24h     -> tokens con más volumen/momentum en 24h
  - /tokens/v2/toporganicscore/24h -> tokens con mejor "organic score"
                                       (Jupiter penaliza volumen de bots)

Solo se usa para DESCUBRIR direcciones de tokens candidatos en Solana; los
datos de mercado que realmente se reportan (precio, liquidez, volumen,
etc.) siguen viniendo de DexScreener para no duplicar lógica de
normalización entre dos formatos distintos.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from config import HTTP_TIMEOUT

logger = logging.getLogger(__name__)

BASE_URL = "https://lite-api.jup.ag/tokens/v2"
DISCOVERY_ENDPOINTS = [
    "/recent",
    "/toptrending/24h",
    "/toporganicscore/24h?limit=100",
]


def _get(url: str) -> Any:
    resp = requests.get(url, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def discover_candidate_addresses() -> list[str]:
    """Devuelve direcciones de tokens candidatos (mints) únicas, combinando
    los listados de recientes/trending/organic score de Jupiter."""
    addresses: dict[str, None] = {}
    for endpoint in DISCOVERY_ENDPOINTS:
        try:
            data = _get(BASE_URL + endpoint)
        except requests.RequestException as exc:
            logger.warning("Fallo al consultar Jupiter %s: %s", endpoint, exc)
            continue
        if not isinstance(data, list):
            continue
        for item in data:
            addr = item.get("id")
            if addr:
                addresses[addr] = None

    logger.info("Jupiter: %d tokens candidatos descubiertos", len(addresses))
    return list(addresses.keys())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    addrs = discover_candidate_addresses()
    print(f"Candidatos encontrados: {len(addrs)}")
    print(addrs[:10])
