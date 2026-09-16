"""Pruebas del historial en SQLite (history_store.py).

Este proyecto no tenía ninguna prueba automática, y son 2,086 líneas que
deciden en qué poner dinero. Estas son las primeras, y las cuatro existen
por el mismo problema real (ver TAREA-ACTUAL.md):

data/history.json guardaba una sola lectura por token y la sobrescribía en
cada corrida (json.dump(..., "w") sobre un dict). A los 27 días de corridas
diarias solo sobrevivía la foto de ayer, y _holders_momentum_score()
terminaba comparando contra "lo último que hubiera" en vez de una ventana
fija de 24h.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import unittest

from history_store import HistoryStore, migrate_from_json

ADDRESS = "LFEJTxJ9yi6ojGDFpjbGfABLbH55Fc3oEK8syJJpump"
HOUR = 3600.0


class TestSumaSinPisar(unittest.TestCase):
    """El bug original: cada corrida sobrescribía la lectura del token
    anterior en vez de sumar una nueva."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.dir.name, "historial.sqlite3")

    def tearDown(self):
        self.dir.cleanup()

    def test_dos_corridas_del_mismo_token_dejan_dos_lecturas(self):
        with HistoryStore(self.db_path) as store:
            store.add_reading(ADDRESS, total_holders=100, ts=time.time() - 2 * HOUR)
            store.add_reading(ADDRESS, total_holders=110, ts=time.time() - 1 * HOUR)
            self.assertEqual(store.count_for(ADDRESS), 2)

    def test_lecturas_de_tokens_distintos_no_se_pisan_entre_si(self):
        with HistoryStore(self.db_path) as store:
            store.add_reading("token-a", total_holders=100)
            store.add_reading("token-b", total_holders=200)
            self.assertEqual(store.count(), 2)

    def test_la_base_sobrevive_a_reabrirse(self):
        """Simula corridas separadas del bot (procesos distintos)."""
        with HistoryStore(self.db_path) as store:
            store.add_reading(ADDRESS, total_holders=100)
        with HistoryStore(self.db_path) as store:
            store.add_reading(ADDRESS, total_holders=110)
            self.assertEqual(store.count_for(ADDRESS), 2)


class TestBusquedaPorVentana(unittest.TestCase):
    """_holders_momentum_score() necesita la lectura más cercana a 24h
    atrás, no "la última que hubiera" (que podía ser de hace una semana)."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.dir.name, "historial.sqlite3")

    def tearDown(self):
        self.dir.cleanup()

    def test_elige_la_lectura_mas_cercana_a_24h_no_la_mas_reciente(self):
        now = time.time()
        with HistoryStore(self.db_path) as store:
            store.add_reading(ADDRESS, total_holders=50, ts=now - 30 * HOUR)  # fuera de tolerancia
            store.add_reading(ADDRESS, total_holders=90, ts=now - 24 * HOUR)  # la correcta
            store.add_reading(ADDRESS, total_holders=99, ts=now - 0.1 * HOUR)  # la más reciente, pero no sirve para 24h
            fila = store.reading_near(ADDRESS, hours_ago=24)
            self.assertEqual(fila["total_holders"], 90)

    def test_sin_lectura_en_la_ventana_devuelve_none(self):
        """Un solo día de datos (o una corrida saltada) no debe inventar
        un momentum comparando contra una ventana equivocada."""
        with HistoryStore(self.db_path) as store:
            store.add_reading(ADDRESS, total_holders=50, ts=time.time() - 1 * HOUR)
            self.assertIsNone(store.reading_near(ADDRESS, hours_ago=24))

    def test_token_sin_ninguna_lectura_devuelve_none(self):
        with HistoryStore(self.db_path) as store:
            self.assertIsNone(store.reading_near("token-nunca-visto", hours_ago=24))

    def test_respeta_la_tolerancia_configurada(self):
        now = time.time()
        with HistoryStore(self.db_path) as store:
            store.add_reading(ADDRESS, total_holders=70, ts=now - 20 * HOUR)
            # A 4h de distancia del objetivo (24h): cabe con tolerancia 6h,
            # no cabe con tolerancia 2h.
            self.assertIsNotNone(store.reading_near(ADDRESS, hours_ago=24, tolerance_h=6))
            self.assertIsNone(store.reading_near(ADDRESS, hours_ago=24, tolerance_h=2))


class TestMigracionDesdeJson(unittest.TestCase):
    """Migrar las 249 lecturas de history.json sin perder ninguna era
    obligatorio antes de tocar el flujo de guardado."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.dir.name, "historial.sqlite3")
        self.json_path = os.path.join(self.dir.name, "history.json")

    def tearDown(self):
        self.dir.cleanup()

    def _escribir_json(self, contenido: dict) -> None:
        with open(self.json_path, "w", encoding="utf-8") as fh:
            json.dump(contenido, fh)

    def test_migra_todas_las_lecturas_del_json(self):
        self._escribir_json(
            {
                "token-a": {"total_holders": 100, "volume_24h": 1000.0, "price_usd": 0.01, "timestamp": 1000.0},
                "token-b": {"total_holders": 200, "volume_24h": 2000.0, "price_usd": 0.02, "timestamp": 2000.0},
            }
        )
        with HistoryStore(self.db_path) as store:
            migradas = migrate_from_json(store, self.json_path)
            self.assertEqual(migradas, 2)
            self.assertEqual(store.count(), 2)

    def test_correr_la_migracion_dos_veces_no_duplica_filas(self):
        self._escribir_json(
            {"token-a": {"total_holders": 100, "volume_24h": 1000.0, "price_usd": 0.01, "timestamp": 1000.0}}
        )
        with HistoryStore(self.db_path) as store:
            migrate_from_json(store, self.json_path)
            segunda_vez = migrate_from_json(store, self.json_path)
            self.assertEqual(segunda_vez, 0, "la segunda corrida no debe migrar nada nuevo")
            self.assertEqual(store.count(), 1, "no debe haber quedado una fila duplicada")

    def test_conserva_el_timestamp_original_de_cada_lectura(self):
        self._escribir_json(
            {"token-a": {"total_holders": 100, "volume_24h": 1000.0, "price_usd": 0.01, "timestamp": 1234.5}}
        )
        with HistoryStore(self.db_path) as store:
            migrate_from_json(store, self.json_path)
            fila = store.reading_near("token-a", hours_ago=(time.time() - 1234.5) / HOUR, tolerance_h=0.01)
            self.assertIsNotNone(fila)
            self.assertEqual(fila["ts"], 1234.5)

    def test_archivo_faltante_no_tumba_la_corrida(self):
        with HistoryStore(self.db_path) as store:
            migradas = migrate_from_json(store, os.path.join(self.dir.name, "no-existe.json"))
            self.assertEqual(migradas, 0)
            self.assertEqual(store.count(), 0)

    def test_archivo_corrupto_no_tumba_la_corrida(self):
        with open(self.json_path, "w", encoding="utf-8") as fh:
            fh.write("{esto no es json")
        with HistoryStore(self.db_path) as store:
            migradas = migrate_from_json(store, self.json_path)
            self.assertEqual(migradas, 0)
            self.assertEqual(store.count(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
