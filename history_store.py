"""Historial de lecturas por token — una fila por corrida, no una por token.

`data/history.json` guardaba una sola lectura por token y la sobrescribía
en cada corrida (`json.dump(..., "w")` sobre un dict). A los 27 días de
corridas diarias solo sobrevivía la foto de ayer: `_holders_momentum_score()`
terminaba comparando contra "lo último que hubiera", que podía ser de hace
un día o de hace una semana.

Este módulo lo reemplaza por `data/historial.sqlite3`, tabla `lecturas`,
que suma una fila por corrida y nunca pisa las anteriores. Así el momentum
se puede calcular contra la lectura más cercana a una ventana fija (24h),
y el dashboard puede mostrar tendencia real en vez de solo el estado de hoy.

Ver TAREA-ACTUAL.md para el porqué y las condiciones obligatorias de la
migración (no perder las 249 lecturas existentes, no borrar history.json
hasta verificar).
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS lecturas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    address         TEXT NOT NULL,
    ts              REAL NOT NULL,
    total_holders   INTEGER,
    volume_24h      REAL,
    price_usd       REAL,
    liquidity_usd   REAL,
    score           REAL,
    passed          INTEGER,
    UNIQUE(address, ts)
);
CREATE INDEX IF NOT EXISTS idx_lecturas_address_ts ON lecturas(address, ts);
"""


class HistoryStore:
    """Wrapper delgado sobre sqlite3 para la tabla `lecturas`.

    Se puede usar como context manager (`with HistoryStore(path) as store:`)
    para asegurar que la conexión se cierre. En Windows, mientras el archivo
    de la base siga abierto no se puede mover ni borrar — cerrar explícito
    importa más ahí que en Linux.
    """

    def __init__(self, path: Path | str):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def __enter__(self) -> "HistoryStore":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def add_reading(
        self,
        address: str,
        *,
        total_holders: int | None = None,
        volume_24h: float | None = None,
        price_usd: float | None = None,
        liquidity_usd: float | None = None,
        score: float | None = None,
        passed: bool | None = None,
        ts: float | None = None,
    ) -> None:
        """Suma una lectura nueva. Nunca pisa una lectura anterior del mismo
        token: cada llamada es una fila nueva (salvo timestamp exactamente
        repetido, ver `migrate_from_json`)."""
        with self._tx() as c:
            c.execute(
                "INSERT OR IGNORE INTO lecturas "
                "(address, ts, total_holders, volume_24h, price_usd, "
                "liquidity_usd, score, passed) VALUES (?,?,?,?,?,?,?,?)",
                (
                    address,
                    ts if ts is not None else time.time(),
                    total_holders,
                    volume_24h,
                    price_usd,
                    liquidity_usd,
                    score,
                    None if passed is None else int(passed),
                ),
            )

    def reading_near(self, address: str, hours_ago: float, tolerance_h: float = 6.0) -> sqlite3.Row | None:
        """Lectura más cercana a `hours_ago` horas atrás, dentro de una
        tolerancia. Devuelve None si no hay ninguna en esa ventana: mejor no
        calcular momentum que inventarlo comparando contra la ventana
        equivocada (ver `_holders_momentum_score` en scoring.py)."""
        target = time.time() - hours_ago * 3600
        lo, hi = target - tolerance_h * 3600, target + tolerance_h * 3600
        cur = self._conn.execute(
            "SELECT * FROM lecturas WHERE address = ? AND ts BETWEEN ? AND ? "
            "ORDER BY ABS(ts - ?) ASC LIMIT 1",
            (address, lo, hi, target),
        )
        return cur.fetchone()

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM lecturas").fetchone()[0]

    def count_for(self, address: str) -> int:
        return self._conn.execute(
            "SELECT COUNT(*) FROM lecturas WHERE address = ?", (address,)
        ).fetchone()[0]


def migrate_from_json(store: HistoryStore, json_path: Path | str) -> int:
    """Migra las lecturas de un `history.json` viejo (un dict {address:
    {total_holders, volume_24h, price_usd, timestamp}}) a la tabla
    `lecturas`. Idempotente: correrla dos veces sobre el mismo archivo no
    duplica filas (UNIQUE(address, ts) + INSERT OR IGNORE).

    Un archivo faltante o corrupto no tumba la corrida: se registra y se
    devuelve 0, igual que el `load_history()` original hacía con
    JSONDecodeError/OSError.
    """
    json_path = Path(json_path)
    if not json_path.exists():
        logger.warning("No se encontró %s, nada que migrar", json_path)
        return 0

    try:
        with open(json_path, encoding="utf-8") as fh:
            old_history = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("No se pudo leer %s (%s), no se migra nada", json_path, exc)
        return 0

    migrated = 0
    for address, reading in old_history.items():
        before = store.count_for(address)
        store.add_reading(
            address,
            total_holders=reading.get("total_holders"),
            volume_24h=reading.get("volume_24h"),
            price_usd=reading.get("price_usd"),
            passed=True,  # history.json solo guardaba tokens que habían pasado filtros
            ts=reading.get("timestamp"),
        )
        if store.count_for(address) > before:
            migrated += 1

    logger.info("Migración desde %s: %d/%d lecturas nuevas (resto ya estaba)", json_path, migrated, len(old_history))
    return migrated


if __name__ == "__main__":
    import config

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    with HistoryStore(config.HISTORY_DB_FILE) as store:
        antes = store.count()
        nuevas = migrate_from_json(store, config.HISTORY_FILE)
        despues = store.count()
        print(f"Filas en {config.HISTORY_DB_FILE.name} antes: {antes}")
        print(f"Lecturas nuevas migradas: {nuevas}")
        print(f"Filas en {config.HISTORY_DB_FILE.name} después: {despues}")
