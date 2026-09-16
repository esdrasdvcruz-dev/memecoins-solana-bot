# TAREA ACTUAL — Historial como serie temporal

Prioridad alta. **Cada día que pasa sin arreglar esto es un día de datos
que no vuelve.** Escrito el 16 sep 2026.

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
