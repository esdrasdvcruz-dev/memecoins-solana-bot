"""
Balances de tokens SPL de una wallet, vía RPC público de Solana
(getTokenAccountsByOwner).

Se usa para detectar cuándo el usuario abre una posición nueva (compra un
token) en su terminal de trading (ej. Axiom): Axiom no tiene API pública,
pero toda compra deja el token comprado en la wallet del usuario on-chain,
así que monitorear la wallet directamente es más confiable que integrarse
con Axiom.
"""

from __future__ import annotations

import logging

from data_sources.solana_rpc import TOKEN_PROGRAM_2022, _rpc_call

logger = logging.getLogger(__name__)

TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"


def _balances_for_program(owner: str, program_id: str) -> dict[str, float]:
    result = _rpc_call(
        "getTokenAccountsByOwner",
        [owner, {"programId": program_id}, {"encoding": "jsonParsed"}],
    )
    balances: dict[str, float] = {}
    if not result:
        return balances
    for account in result.get("value", []):
        try:
            info = account["account"]["data"]["parsed"]["info"]
            mint = info["mint"]
            amount = float(info["tokenAmount"]["uiAmount"] or 0)
        except (KeyError, TypeError):
            continue
        balances[mint] = balances.get(mint, 0) + amount
    return balances


def get_token_balances(owner_address: str) -> dict[str, float]:
    """Balances actuales de todos los tokens SPL (clásico + Token-2022) de
    la wallet dada, incluyendo solo mints con balance > 0."""
    balances = _balances_for_program(owner_address, TOKEN_PROGRAM)
    balances.update(_balances_for_program(owner_address, TOKEN_PROGRAM_2022))
    return {mint: amt for mint, amt in balances.items() if amt > 0}


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    owner = sys.argv[1] if len(sys.argv) > 1 else ""
    if not owner:
        print("Uso: python -m data_sources.wallet <wallet_address>")
    else:
        print(get_token_balances(owner))
