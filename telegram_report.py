"""
Envío del reporte diario por Telegram (Bot API, HTML parse_mode).

Se manda un mensaje por token en vez de un único mensaje gigante para no
chocar con el límite de 4096 caracteres de sendMessage, más un mensaje de
cabecera y uno de cierre con la advertencia de riesgo.
"""

from __future__ import annotations

import html
import logging
import time
import urllib.parse
from datetime import datetime, timezone

import requests

from config import HTTP_TIMEOUT, PUBLIC_DASHBOARD_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

API_URL = "https://api.telegram.org/bot{token}/sendMessage"
SECONDS_BETWEEN_MESSAGES = 1.1  # Telegram permite ~1 msg/seg por chat

RISK_WARNING = (
    "⚠️ <b>Advertencia de riesgo</b>\n"
    "Esta información es generada automáticamente y NO es asesoría financiera. "
    "Los memecoins en Solana son extremadamente volátiles y de alto riesgo; "
    "incluso pasando estos filtros pueden perder todo su valor. "
    "Verifica siempre por tu cuenta antes de invertir y nunca arriesgues más "
    "de lo que estás dispuesto a perder."
)


def _fmt_usd(value: float | None) -> str:
    if value is None:
        return "N/D"
    return f"${value:,.0f}" if value >= 1000 else f"${value:,.2f}"


def _fmt_price(value: float | None) -> str:
    if value is None:
        return "N/D"
    if value < 0.01:
        return f"${value:.8f}"
    return f"${value:,.4f}"


def _fmt_age(hours: float | None) -> str:
    if hours is None:
        return "N/D"
    days = hours / 24
    if days >= 1:
        return f"{days:.1f} días"
    return f"{hours:.1f} horas"


def _bubble_map_url(token: dict) -> str:
    """Link al mapa de burbujas público, con el token resaltado en el
    buscador automáticamente (ver el manejo de ?q= en dashboard.py)."""
    query = token.get("symbol") or token.get("address") or ""
    return f"{PUBLIC_DASHBOARD_URL}?q={urllib.parse.quote(str(query))}"


def format_header(count: int) -> str:
    today = datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y")
    return (
        f"\U0001f4ca <b>Reporte diario memecoins Solana</b> — {today}\n"
        f"Top {count} tokens que pasaron los filtros de confiabilidad."
    )


def format_token_message(token: dict, rank: int) -> str:
    name = html.escape(str(token.get("name") or "?"))
    symbol = html.escape(str(token.get("symbol") or "?"))
    address = token.get("address", "")
    url = token.get("url") or f"https://dexscreener.com/solana/{token.get('pair_address', address)}"

    lines = [
        f"<b>#{rank} {name} (${symbol})</b> — Score: <b>{token['score']}/100</b>",
        f"\U0001f552 Edad: {_fmt_age(token.get('age_hours'))}",
        f"\U0001f4b5 Precio: {_fmt_price(token.get('price_usd'))}",
        f"\U0001f3e6 Market Cap: {_fmt_usd(token.get('market_cap'))}",
        f"\U0001f4a7 Liquidez: {_fmt_usd(token.get('liquidity_usd'))}",
        f"\U0001f4c8 Volumen 24h: {_fmt_usd(token.get('volume_24h'))}",
        f"\U0001f4c9 Cambio 24h: {token.get('price_change_24h', 0):+.1f}%",
        f"\U0001f465 Holders: {token.get('total_holders', 'N/D')}",
        f"\U0001f512 Seguridad (RugCheck): {token['score_breakdown']['security']}/100 "
        f"(top10 holders: {token.get('top10_holder_pct', 'N/D')}%, LP bloqueada: {token.get('lp_locked_pct', 'N/D')}%)",
    ]

    risks = token.get("risks") or []
    if risks:
        flags = "; ".join(html.escape(r["name"]) for r in risks if r.get("name"))
        lines.append(f"\U0001f6a9 Banderas rojas: {flags}")
    else:
        lines.append("✅ Sin banderas rojas reportadas por RugCheck")

    lines.append(f"\U0001f517 <a href=\"{html.escape(url)}\">Ver en DexScreener</a>")
    lines.append(f"\U0001fae7 <a href=\"{html.escape(_bubble_map_url(token))}\">Ver en el mapa de burbujas</a>")
    lines.append(f"<code>{html.escape(address)}</code>")

    return "\n".join(lines)


def _send_message(text: str, disable_preview: bool = True) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurados en .env")
        return False

    url = API_URL.format(token=TELEGRAM_BOT_TOKEN)
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": disable_preview,
    }
    try:
        resp = requests.post(url, json=payload, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        body = getattr(exc.response, "text", "")
        logger.error("Fallo al enviar mensaje a Telegram: %s %s", exc, body)
        return False


def send_error_alert(error_traceback: str) -> None:
    """Avisa por Telegram que la corrida diaria falló. Se manda un extracto
    corto del traceback (Telegram limita cada mensaje a 4096 caracteres)."""
    snippet = error_traceback.strip()[-3000:]
    text = (
        "\U0001f6a8 <b>El bot de memecoins falló durante la corrida de hoy</b>\n"
        "No se pudo generar el reporte. Detalle del error:\n"
        f"<pre>{html.escape(snippet)}</pre>\n"
        "Revisa <code>data/bot.log</code> para el traceback completo."
    )
    _send_message(text)


def format_live_analysis_message(token: dict, fail_reasons: list[str] | None) -> str:
    name = html.escape(str(token.get("name") or "?"))
    symbol = html.escape(str(token.get("symbol") or "?"))
    address = token.get("address", "")
    url = token.get("url") or f"https://dexscreener.com/solana/{token.get('pair_address', address)}"

    lines = [
        "\U0001f6a8 <b>Nueva posición detectada en tu wallet</b>",
        f"<b>{name} (${symbol})</b>",
    ]

    score = token.get("score")
    if score is not None:
        lines.append(f"Score: <b>{score}/100</b>")

    lines += [
        f"\U0001f552 Edad: {_fmt_age(token.get('age_hours'))}",
        f"\U0001f4b5 Precio: {_fmt_price(token.get('price_usd'))}",
        f"\U0001f3e6 Market Cap: {_fmt_usd(token.get('market_cap'))}",
        f"\U0001f4a7 Liquidez: {_fmt_usd(token.get('liquidity_usd'))}",
        f"\U0001f4c8 Volumen 24h: {_fmt_usd(token.get('volume_24h'))}",
        f"\U0001f4c9 Cambio 24h: {token.get('price_change_24h', 0):+.1f}%",
        f"\U0001f465 Holders: {token.get('total_holders', 'N/D')}",
    ]

    security_score = (token.get("score_breakdown") or {}).get("security")
    if security_score is not None:
        lines.append(
            f"\U0001f512 Seguridad (RugCheck): {security_score}/100 "
            f"(top10 holders: {token.get('top10_holder_pct', 'N/D')}%, "
            f"LP bloqueada: {token.get('lp_locked_pct', 'N/D')}%)"
        )
    else:
        lines.append("\U0001f512 Seguridad: sin datos disponibles todavía (token muy nuevo)")

    risks = token.get("risks") or []
    if risks:
        flags = "; ".join(html.escape(r["name"]) for r in risks if r.get("name"))
        lines.append(f"\U0001f6a9 Banderas rojas: {flags}")

    if fail_reasons:
        reasons = "; ".join(html.escape(r) for r in fail_reasons)
        lines.append(f"⚠️ <b>No pasaría los filtros de confiabilidad del bot:</b> {reasons}")
    else:
        lines.append("✅ Pasaría todos los filtros de confiabilidad del bot")

    lines.append(f"\U0001f517 <a href=\"{html.escape(url)}\">Ver en DexScreener</a>")
    lines.append(f"\U0001fae7 <a href=\"{html.escape(_bubble_map_url(token))}\">Ver en el mapa de burbujas</a>")
    lines.append(f"<code>{html.escape(address)}</code>")

    return "\n".join(lines)


def send_live_analysis(
    token: dict, fail_reasons: list[str] | None = None, incomplete: bool = False
) -> None:
    """Manda el análisis en vivo de una posición recién detectada en la
    wallet. `incomplete=True` cuando DexScreener todavía no tiene datos de
    mercado del token (par demasiado nuevo)."""
    if incomplete:
        address = token.get("address", "")
        _send_message(
            "\U0001f6a8 <b>Nueva posición detectada en tu wallet</b>\n"
            f"<code>{html.escape(address)}</code>\n"
            "No se encontraron datos de mercado en DexScreener todavía "
            "(par muy nuevo o sin liquidez indexada)."
        )
        return
    _send_message(format_live_analysis_message(token, fail_reasons))


def send_report(tokens: list[dict]) -> None:
    if not tokens:
        _send_message(
            "\U0001f4ca <b>Reporte diario memecoins Solana</b>\n"
            "Hoy ningún token cumplió todos los filtros de confiabilidad. "
            "Vuelve a intentar mañana."
        )
        _send_message(RISK_WARNING)
        return

    _send_message(format_header(len(tokens)))
    time.sleep(SECONDS_BETWEEN_MESSAGES)

    for i, token in enumerate(tokens, start=1):
        ok = _send_message(format_token_message(token, i))
        if not ok:
            logger.warning("No se pudo enviar el token #%d (%s)", i, token.get("symbol"))
        time.sleep(SECONDS_BETWEEN_MESSAGES)

    _send_message(RISK_WARNING)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    fake_token = {
        "name": "Example Token <3",
        "symbol": "EXM",
        "address": "ExAmPLE111111111111111111111111111111111",
        "url": "https://dexscreener.com/solana/example",
        "score": 78,
        "score_breakdown": {"security": 85, "momentum": 60, "liquidity": 90},
        "age_hours": 36.5,
        "price_usd": 0.00001234,
        "market_cap": 1_200_000,
        "liquidity_usd": 150_000,
        "volume_24h": 400_000,
        "price_change_24h": 12.5,
        "total_holders": 1234,
        "top10_holder_pct": 18.2,
        "lp_locked_pct": 100,
        "risks": [],
    }

    print("--- Vista previa del mensaje (sin enviar) ---")
    print(format_header(1))
    print()
    print(format_token_message(fake_token, 1))
    print()
    print(RISK_WARNING)

    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("\n--- Enviando prueba real a Telegram ---")
        send_report([fake_token])
    else:
        print("\n(TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID no configurados, no se envía nada real)")
