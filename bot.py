"""
Bot de análisis diario de memecoins en Solana.

Flujo:
  1. Descubre tokens candidatos en Solana (DexScreener + Jupiter).
  2. Trae datos de mercado (precio, liquidez, volumen, market cap).
  3. Preselecciona con filtros baratos (liquidez, volumen, edad) para no
     gastar el rate limit de RugCheck en tokens que van a fallar igual.
  4. Consulta RugCheck para la info de seguridad de los preseleccionados
     (con RPC de Solana como respaldo si RugCheck no tiene datos).
  5. Aplica todos los filtros de confiabilidad y calcula el score 0-100.
  6. Envía el top N por Telegram.

Si algo revienta a mitad de camino (una API caída, un bug, etc.), se
manda un aviso de error por Telegram además de quedar registrado en
data/bot.log, para enterarse sin tener que ir a revisar el log a mano.

Uso manual:   python bot.py
Uso programado: ver README.md (Programador de tareas de Windows).
"""

from __future__ import annotations

import logging
import sys
import traceback

import config
from dashboard import render_dashboard
from data_sources import dexscreener, jupiter, rugcheck, solana_rpc
from publish_dashboard import publish_dashboard
from scoring import cheap_prefilter, evaluate_tokens
from telegram_report import send_error_alert, send_report

_handlers = [logging.FileHandler(config.LOG_FILE, encoding="utf-8")]
if sys.stdout is not None:
    # Al ejecutarse con pythonw.exe (sin consola, útil para la tarea
    # programada) sys.stdout es None y un StreamHandler ahí rompería el
    # logging; en ese caso solo se escribe al archivo data/bot.log.
    _handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=_handlers,
)
logger = logging.getLogger("bot")


def get_security_info(addresses: list[str]) -> dict[str, dict]:
    """Info de seguridad por token: RugCheck primero, RPC de Solana como
    respaldo para los que RugCheck no tenga indexados."""
    security = rugcheck.get_security_info_bulk(addresses)

    missing = [a for a in addresses if a not in security]
    if missing:
        logger.info("RugCheck sin datos para %d tokens, probando respaldo RPC", len(missing))
        for addr in missing:
            fallback = solana_rpc.get_security_info_fallback(addr)
            if fallback:
                security[addr] = fallback

    return security


def run() -> list[dict]:
    logger.info("=== Iniciando análisis diario de memecoins en Solana ===")

    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.error(
            "Faltan TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID en .env. "
            "Revisa el README para configurarlos."
        )
        sys.exit(1)

    addresses = set(dexscreener.discover_candidate_addresses())
    addresses.update(jupiter.discover_candidate_addresses())
    addresses = list(addresses)
    logger.info("Total de candidatos únicos combinando fuentes: %d", len(addresses))
    if not addresses:
        logger.warning("No se descubrieron tokens candidatos, se aborta esta corrida")
        send_report([])
        render_dashboard([], config.DASHBOARD_FILE)
        publish_dashboard()
        return []

    market_tokens = dexscreener.get_market_data(addresses)
    preselected = cheap_prefilter(market_tokens)

    if not preselected:
        logger.info("Ningún token pasó la preselección barata")
        send_report([])
        render_dashboard([], config.DASHBOARD_FILE)
        publish_dashboard()
        return []

    security_by_address = get_security_info([t["address"] for t in preselected])
    passed, evaluated = evaluate_tokens(preselected, security_by_address)
    render_dashboard(evaluated, config.DASHBOARD_FILE)
    publish_dashboard()

    top_n = passed[: config.TOP_N_REPORT]
    logger.info("Enviando reporte con %d tokens por Telegram", len(top_n))
    send_report(top_n)

    logger.info("=== Análisis diario finalizado ===")
    return top_n


def main() -> None:
    try:
        run()
    except SystemExit:
        raise  # salidas controladas (ej. falta configurar .env), no son un "crash"
    except Exception:
        logger.exception("Fallo no controlado durante la corrida diaria")
        try:
            send_error_alert(traceback.format_exc())
        except Exception:
            logger.exception("Además falló el intento de avisar el error por Telegram")
        sys.exit(1)


if __name__ == "__main__":
    main()
