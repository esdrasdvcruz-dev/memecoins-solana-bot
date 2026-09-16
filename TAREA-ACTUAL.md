# PENDIENTES del bot de memecoins

Actualizado el 16 sep 2026. Lo de arriba es lo siguiente que toca.

## Hecho (no rehacer)

- **Historial como serie temporal.** `data/historial.sqlite3`, tabla
  `lecturas`, con índice `(address, ts)`. Las 249 lecturas de
  `history.json` se migraron **conservando sus fechas originales**:
  verificado, 25 días distintos del 20/08 al 16/09. `history.json` se
  conserva intacto como respaldo. 12 pruebas en `test_history_store.py`.
- **La lectura previa se busca por ventana de tiempo** (24h ± 6h), no por
  "la última corrida". Si no hay nada en la ventana devuelve neutral en
  vez de inventar un momentum.
- **Tabla de trincheras.** Dos vistas en pestañas: Trincheras (tabla) y
  Mapa de burbujas. La tabla se arma **en Python** y viaja escrita en el
  HTML, así que la página se lee aunque d3 no cargue desde el CDN.
  10 columnas, foto del token a la izquierda, montos compactos
  (`$1.2M`), y `Riesgo` en una palabra (Seguro / Cuidado / Peligro)
  fundiendo seguridad + LP bloqueada + top 10 holders, con el detalle en
  el `title`.

## 1. Panel "qué cambió desde ayer"

Lo primero que uno quiere ver al abrir. Ya es posible porque el
historial guarda serie.

Qué mostrar, comparando la corrida de hoy contra la de ayer:
- tokens que **entraron** al grupo de los que pasan filtros
- tokens que **salieron**
- **saltos de score** de más de ~10 puntos, arriba o abajo
- tokens **nuevos**, nunca vistos antes

Va arriba de la tabla, en la vista de Trincheras. Usa
`history_store.reading_near()` con 24h.

## 2. Normalizar el momentum por las horas reales

Hoy la ventana es rígida: 24h ± 6h. Si un día se salta la corrida, o si
el bot corre dos veces el mismo día, no encuentra lectura y el momentum
queda neutral. **Medido el 16 sep: de 80 tokens, 0 encontraron lectura
previa en la ventana** — porque ese día el bot corrió a las 12:10 y a
las 21:49, o sea 9.6h de separación.

Arreglo propuesto: tomar la lectura anterior **sea cual sea su
antigüedad** y normalizar el crecimiento por las horas transcurridas
(`crecimiento por 24h = crecimiento × 24 ÷ horas`). Así una lectura de
9.6h y otra de 36h dan momentums comparables, y casi nunca sale neutral.

Lo actual es defendible (prefiere callarse antes que equivocarse), así
que esto es mejora, no urgencia.

## 3. Ruido en el log de `watch_wallet.py`

Corre cada 2 minutos y escribe "Sin posiciones nuevas" siempre: ~720
líneas al día. Cuando de verdad pase algo va a estar enterrado. Debe
registrar solo cuando algo cambia.

## 4. Sparklines de 30 días — esperar

Tienen sentido cuando el historial junte ~30 días de serie. Al 16 sep
hay 25 días acumulados, así que **alrededor del 20 de octubre de 2026**.
No antes: una sparkline con 3 puntos engaña más de lo que informa.

## 5. Ideas sin decidir

- Ordenar por "riesgo" y por "entraron hoy" desde el buscador.
- Enlace directo desde el reporte de Telegram a la fila del token en la
  tabla (hoy el deep link `?q=SYMBOL` solo resalta en el mapa).

## Reglas que no cambian

1. Credenciales en `.env`. `config.py` las lee con `os.getenv()` y no
   guarda valores.
2. `data/` no se sube al repositorio.
3. RugCheck limita a ~15 peticiones por minuto. **Un 429 no se
   reintenta**: insistir alarga el castigo. Hay un limitador con
   enfriamiento listo para trasplantar en
   `C:\Users\perri\Documents\nft-signal-bot\src\sources\base.py`.
4. No mover los umbrales de los filtros sin antes verificar que el
   número que miden esté bien medido. Lección del bot de NFT: un filtro
   calibrado contra un número mal medido rechaza todo para siempre, y se
   ve igual que un mercado malo.
5. `python dashboard.py` escribe en `data/dashboard_ejemplo.html`, NO en
   el dashboard real. El real solo lo regenera `bot.py` con datos
   verdaderos.
