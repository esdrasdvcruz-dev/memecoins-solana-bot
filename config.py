"""Configuración central del bot: variables de entorno y umbrales de filtrado."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Ruta explícita al .env (en vez de depender del directorio actual): así el
# bot funciona igual ejecutado a mano o desde el Programador de tareas de
# Windows, sin importar cuál sea el "directorio de inicio" configurado.
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

HISTORY_FILE = DATA_DIR / "history.json"
LOG_FILE = DATA_DIR / "bot.log"
DASHBOARD_FILE = BASE_DIR / "dashboard.html"

# --- Publicación pública del dashboard (ver publish_dashboard.py) ---
PUBLIC_DASHBOARD_URL = "https://esdrasdvcruz-dev.github.io/memecoins-solana-bot/"

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# --- Cadena a analizar ---
CHAIN_ID = "solana"

# --- Wallet a vigilar para análisis en vivo (watch_wallet.py) ---
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "")
WALLET_POSITIONS_FILE = DATA_DIR / "wallet_positions.json"

# --- Filtros de confiabilidad (requisito #2) ---
MIN_LIQUIDITY_USD = float(os.getenv("MIN_LIQUIDITY_USD", 50_000))
MIN_VOLUME_24H_USD = float(os.getenv("MIN_VOLUME_24H_USD", 100_000))
MIN_AGE_HOURS = float(os.getenv("MIN_AGE_HOURS", 24))
MIN_HOLDERS = int(os.getenv("MIN_HOLDERS", 500))
MAX_TOP10_HOLDER_PCT = float(os.getenv("MAX_TOP10_HOLDER_PCT", 30))
MIN_LP_LOCKED_PCT = float(os.getenv("MIN_LP_LOCKED_PCT", 80))

# --- Reporte ---
TOP_N_REPORT = int(os.getenv("TOP_N_REPORT", 10))

# --- Red / rate limiting ---
HTTP_TIMEOUT = 15
RUGCHECK_MAX_REQUESTS_PER_MINUTE = 15  # observado en headers X-Rate-Limit-Limit
