"""
Vigilancia de la wallet para análisis en vivo cuando se abre una operación.

Axiom (axiom.trade) no tiene API pública para leer tus posiciones abiertas,
pero toda compra es una transacción on-chain que deja el token en tu
wallet. Por eso, en vez de integrarse con Axiom, este script monitorea
directamente tu wallet de Solana:

  1. Lee el snapshot de balances guardado en data/wallet_positions.json
     (de la corrida anterior).
  2. Consulta los balances de tokens actuales de la wallet vía RPC de
     Solana (data_sources/wallet.py).
  3. Compara: cualquier mint con balance > 0 que antes estaba en 0 (o no
     existía) es una posición nueva recién abierta.
  4. Por cada posición nueva corre el mismo análisis que el reporte diario
     (mercado + seguridad + score) y lo manda por Telegram, SIN aplicar los
     filtros de confiabilidad como criterio de descarte: la posición ya
     está abierta, así que se informa el resultado igual pase o no los
     filtros (indicando cuáles no pasaría).
  5. Guarda el snapshot actual para la próxima corrida.

Pensado para correr cada pocos minutos vía el Programador de tareas de
Windows (igual que bot.py, pero con más frecuencia). Solo avisa una vez por
posición nueva: mientras el token siga en la wallet no se vuelve a avisar,
y si vuelve a comprarse después de haberlo vendido del todo (balance a 0),
se vuelve a tratar como posición nueva.

Uso manual: python watch_wallet.py
"""

from __future__ import annotations

import json
import logging
import sys
import traceback

import config
from bot import get_security_info
from data_sources import dexscreener, wallet
from scoring import _age_hours, check_filters, load_history, score_token
from telegram_report import send_error_alert, send_live_analysis

_handlers = [logging.FileHandler(config.LOG_FILE, encoding="utf-8")]
if sys.stdout is not None:
    _handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=_handlers,
)
logger = logging.getLogger("watch_wallet")


def load_known_positions() -> dict[str, float]:
    if not config.WALLET_POSITIONS_FILE.exists():
        return {}
    try:
        with open(config.WALLET_POSITIONS_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("No se pudo leer wallet_positions.json (%s), se ignora", exc)
        return {}


def save_known_positions(positions: dict[str, float]) -> None:
    with open(config.WALLET_POSITIONS_FILE, "w", encoding="utf-8") as fh:
        json.dump(positions, fh, indent=2)


def analyze_new_position(address: str) -> None:
    market = dexscreener.get_market_data([address])
    if not market:
        logger.warning(
            "Sin datos de mercado en DexScreener para %s, aviso sin análisis completo", address
        )
        send_live_analysis({"address": address}, incomplete=True)
        return

    token = market[0]
    security = get_security_info([address]).get(address)
    if security:
        token = {**token, **security}
    token["age_hours"] = _age_hours(token.get("pair_created_at_ms"))

    if security:
        history = load_history()
        token = score_token(token, history.get(address))
        fail_reasons = check_filters(token)
    else:
        fail_reasons = ["sin datos de seguridad disponibles (ni RugCheck ni RPC)"]

    logger.info(
        "Análisis en vivo de %s (%s): score=%s, filtros_fallidos=%s",
        token.get("symbol"),
        address,
        token.get("score"),
        len(fail_reasons),
    )
    send_live_analysis(token, fail_reasons=fail_reasons)


def run() -> None:
    if not config.WALLET_ADDRESS:
        logger.error("Falta WALLET_ADDRESS en .env. Revisa el README para configurarlo.")
        sys.exit(1)

    logger.info("=== Chequeo de wallet para posiciones nuevas ===")
    is_first_run = not config.WALLET_POSITIONS_FILE.exists()
    known = load_known_positions()
    current = wallet.get_token_balances(config.WALLET_ADDRESS)

    if is_first_run:
        logger.info(
            "Primera corrida: se guarda el snapshot inicial de %d tokens sin avisar "
            "(son posiciones que ya tenías antes de activar esta función)",
            len(current),
        )
        save_known_positions(current)
        logger.info("=== Chequeo de wallet finalizado ===")
        return

    new_mints = [mint for mint, amount in current.items() if amount > 0 and known.get(mint, 0) <= 0]

    if new_mints:
        logger.info("Posiciones nuevas detectadas: %s", new_mints)
        for mint in new_mints:
            try:
                analyze_new_position(mint)
            except Exception:
                logger.exception("Fallo analizando posición nueva %s", mint)
    else:
        logger.info("Sin posiciones nuevas (%d tokens en la wallet)", len(current))

    save_known_positions(current)
    logger.info("=== Chequeo de wallet finalizado ===")


def main() -> None:
    try:
        run()
    except SystemExit:
        raise
    except Exception:
        logger.exception("Fallo no controlado en el chequeo de wallet")
        try:
            send_error_alert(traceback.format_exc())
        except Exception:
            logger.exception("Además falló el intento de avisar el error por Telegram")
        sys.exit(1)


if __name__ == "__main__":
    main()
