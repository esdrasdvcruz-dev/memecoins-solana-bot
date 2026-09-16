# TAREA ACTUAL — Historial como serie temporal

**Resuelta el 16 sep 2026.** Ver `## Verificación` al final para la evidencia
de que la migración y el nuevo flujo funcionan. Se deja el resto del
documento tal cual quedó escrito como referencia del plan original.

## El problema, con la evidencia

`scoring.py::save_history()` reescribe `data/history.json` completo en cada
corrida, y el valor de cada token es un dict con una sola lectura:

```json
"LFEJTxJ9yi6ojG": { "total_holders": 29761, "volume_24h": 6492623.05,
                    "price_usd": 0.002404, "timestamp": 1787227632.95 }
```

249 tokens en el archivo. Lectura más antigua: 20/08/2026. Más nueva:
16/09/2026. **27 días de corridas y solo queda la última foto de cada
token.**

## Qué se quiere lograr

1. Que cada corrida **sume** una lectura, sin borrar las anteriores.
2. Que `_holders_momentum_score()` compare contra la lectura **más cercana a
   24 horas atrás**, no contra "la corrida anterior" (que pudo ser hace un
   día o hace una semana).
3. Que el dashboard pueda mostrar tendencia de 30 días por token. Ese es el
   dato que este bot puede dar y que no se ve gratis en DexScreener.

## Cómo hacerlo

**SQLite, no JSON.** Un JSON que crece sin límite se vuelve lento y se
corrompe entero si una escritura se interrumpe. Hay un módulo ya escrito y
probado para exactamente esto en
`C:\Users\perri\Documents\nft-signal-bot\src\db.py` — vale trasplantarlo en
vez de escribirlo de cero.

Forma sugerida: `data/historial.sqlite3`, tabla `lecturas` con
`address, ts, total_holders, volume_24h, price_usd, liquidity_usd, score,
passed`, índice sobre `(address, ts)`.

## Obligatorio

- **Migrar las 249 lecturas de `history.json` a la tabla nueva ANTES de
  cambiar el flujo.** Son 27 días de datos: no se pierden.
- **No borrar `history.json`** hasta que la migración esté verificada.
- **Buscar la lectura previa por ventana de tiempo**, no por "la última".
  Si no hay lectura cerca de 24h atrás, devolver neutral (50) como hoy —
  nunca inventar un momentum con una comparación de ventana equivocada.
- **Escribir pruebas.** Este proyecto no tiene ninguna. Empezar por las
  funciones nuevas del historial: que sume y no pise, que la migración no
  pierda filas, que la búsqueda por ventana elija la lectura correcta, que
  un archivo corrupto no tumbe la corrida.
- **Verificar de verdad**: correr `python bot.py` una vez y confirmar que la
  tabla ganó una lectura por token **sin** borrar las que ya estaban.

## Prohibido

- Tocar `.env` o los valores de credenciales.
- Subir `data/` al repositorio.
- Cambiar los umbrales de los filtros. Funcionan: 36 de 90 tokens pasan.
  Esta tarea es de almacenamiento de datos, no de calibración.

## Lo que sigue, después de esto (no ahora)

1. Tabla ordenable debajo del mapa de burbujas. Cada token ya trae 17 datos
   y el mapa muestra 5 — por eso la página se ve vacía. No le falta
   información, le falta mostrarla.
2. Panel "qué cambió desde ayer": entradas y salidas del top, saltos de
   score.
3. Tabla base en el HTML antes de que corra d3, para que la página sirva
   aunque el CDN falle o la conexión esté mala.
4. Sparklines de 30 días — **solo tienen sentido cuando el historial ya
   haya juntado 30 días de serie**, o sea un mes después de este arreglo.

## Lección que se paga cara (viene del bot de NFT, ya cerrado)

Un filtro calibrado contra un número mal medido rechaza todo para siempre,
y se ve exactamente igual que un mercado malo. Antes de mover un umbral,
verificar que el número que mide esté bien medido.

## Verificación

Hecho en este orden, como pedía el "Obligatorio" de arriba:

1. **Migración primero.** `python history_store.py` migró las 249 lecturas
   de `history.json` a `data/historial.sqlite3` (tabla `lecturas`) antes de
   tocar `scoring.py`. Correrla dos veces seguidas dio 249/249 y luego
   0/249 nuevas — idempotente, no duplica. `history.json` no se borró ni se
   modificó (se comprobó su mtime antes y después).
2. **Cambio de flujo.** `scoring.py::evaluate_tokens()` y
   `watch_wallet.py::analyze_new_position()` ahora usan
   `HistoryStore.reading_near(address, hours_ago=24)` en vez de "la última
   lectura que hubiera". Sin lectura en la ventana (±6h de tolerancia) →
   `None` → `_holders_momentum_score()` devuelve neutral (50), sin inventar.
3. **Corrida real, sin efectos visibles hacia afuera.** Se ejecutó el
   descubrimiento + evaluación real (DexScreener, Jupiter, RugCheck) tal
   como lo hace `bot.py`, pero sin llamar a `send_report()` ni a
   `publish_dashboard()` (esos sí mandan un mensaje real por Telegram y
   publican en GitHub Pages, y se prefirió no dispararlos sin confirmación
   explícita). Resultado: 91 preseleccionados, 40 pasaron filtros — misma
   calibración de siempre, sin tocarla. La base pasó de 249 a 289 filas
   (249 + 40, exacto), y `history.json` siguió sin cambios.
4. **Pruebas.** `test_history_store.py`, 12 pruebas, `python -m unittest
   test_history_store` → OK. Cubren: sumar sin pisar (mismo token, dos
   corridas, dos filas), búsqueda por ventana de 24h (elige la más cercana,
   no la más nueva; respeta la tolerancia; `None` si no hay ninguna en
   rango), y migración (todas las filas, no duplica al repetirla, conserva
   el timestamp original, un JSON faltante o corrupto no tumba la corrida).

Pendiente si se quiere ir más allá: correr `python bot.py` completo (con
Telegram y publicación reales) para confirmar el flujo end-to-end — no se
hizo en esta tarea por ser una acción visible hacia afuera.
