# Bot de Análisis de Memecoins en Solana

## Qué hace

Corre una vez al día, descubre memecoins en Solana, les aplica 5 filtros de
confiabilidad, les calcula un score de 0 a 100, manda el top 10 por Telegram
y publica un mapa de burbujas en GitHub Pages.

**Funciona y está en producción.** En la corrida del 16 sep 2026: 90 tokens
evaluados, 36 pasaron los filtros. Esa tasa de aprobación del 40% es sana —
los filtros discriminan sin rechazar todo.

## Estructura

```
bot.py                  # orquestador del reporte diario:  python bot.py
watch_wallet.py         # vigila la wallet y analiza posiciones nuevas
dashboard.py            # genera dashboard.html (mapa de burbujas, d3 circle packing)
publish_dashboard.py    # publica dashboard.html en GitHub Pages
serve_dashboard.py      # sirve dashboard.html por WiFi local (para el celular)
abrir_mapa_movil.bat    # doble clic = corre serve_dashboard.py
config.py               # lee variables de entorno + umbrales de filtrado
scoring.py              # filtros de confiabilidad + score 0-100 + historial
telegram_report.py      # formato y envío del reporte
data_sources/
  dexscreener.py        # descubrimiento + datos de mercado
  jupiter.py            # descubrimiento adicional (recientes/trending)
  rugcheck.py           # seguridad, holders, mint/freeze authority
  solana_rpc.py         # respaldo si RugCheck no tiene el token
  wallet.py             # balances SPL de una wallet
data/
  history.json          # historial (ver PROBLEMA CONOCIDO abajo)
  wallet_positions.json # último snapshot de la wallet
  bot.log               # log de cada corrida
```

Cada módulo de `data_sources/` se puede correr solo para probarlo:
`python -m data_sources.rugcheck`

## Los filtros (config.py, ajustables por variables de entorno)

| Umbral | Valor | Qué protege |
|---|---|---|
| `MIN_LIQUIDITY_USD` | 50,000 | Que se pueda salir sin mover el precio |
| `MIN_VOLUME_24H_USD` | 100,000 | Que haya contrapartes |
| `MIN_AGE_HOURS` | 24 | Descarta lanzamientos de horas |
| `MIN_HOLDERS` | 500 | Distribución mínima |
| `MAX_TOP10_HOLDER_PCT` | 30 | Que 10 wallets no tengan el token secuestrado |
| `MIN_LP_LOCKED_PCT` | 80 | Anti-rug: LP bloqueada o quemada |

El score es `0.4 x seguridad + 0.3 x momentum + 0.3 x liquidez`. El momentum
es el promedio de momentum de volumen y momentum de holders.

## PROBLEMA CONOCIDO — es la tarea prioritaria

**`data/history.json` guarda UNA sola lectura por token y la sobrescribe en
cada corrida.** `save_history()` reescribe el archivo completo con
`json.dump(..., "w")`, y el valor de cada token es un dict, no una lista:

```json
{ "total_holders": 29761, "volume_24h": 6492623.05,
  "price_usd": 0.002404, "timestamp": 1787227632.95 }
```

Medido el 16 sep 2026: 249 tokens, lectura más antigua del 20 de agosto,
más nueva del 16 de septiembre. **27 días de corridas diarias y solo
sobrevive la foto del último día.**

Consecuencias:
1. `_holders_momentum_score()` compara contra "la corrida anterior", que
   puede haber sido hace un día o hace una semana. No es una ventana fija.
2. El dashboard no puede mostrar tendencia, solo el estado de hoy — y la
   tendencia de 30 días es el único dato que este bot puede dar y que no se
   ve gratis en DexScreener.

Ver `TAREA-ACTUAL.md` para el plan de arreglo.

## Reglas no negociables

1. **Las credenciales van en `.env`, nunca en un archivo del repositorio.**
   `config.py` las lee con `os.getenv()` y no guarda valores: por eso sí
   puede estar en git.
2. **`data/` no se sube.** Son datos generados, no código.
3. **RugCheck limita a ~15 peticiones por minuto** (visto en sus cabeceras
   `X-Rate-Limit-Limit`). Respetarlo. Hay un limitador con enfriamiento ante
   un 429 listo para trasplantar en
   `C:\Users\perri\Documents\nft-signal-bot\src\sources\base.py`.
   Regla aprendida ahí: **un 429 no se reintenta** — insistir alarga el
   castigo del servidor.
4. **`publish_dashboard.py` usa una deploy key SSH dedicada** (solo escritura
   en este repo, host `github-memecoins-deploy` en `~/.ssh/config`) y un
   worktree local `.gh-pages-worktree`. Se configuró una vez a mano; el
   módulo no lo crea. Es así a propósito: con HTTPS, Git Credential Manager
   se cuelga pidiendo login en un proceso sin sesión interactiva.
5. **Si la publicación del dashboard falla, la corrida NO se interrumpe.** Se
   registra en el log y el reporte de Telegram sale igual.
6. **Esto no es asesoría financiera** y el reporte siempre lleva su
   advertencia de riesgo. No quitarla.

## Tareas programadas en Windows

- Reporte diario: 8:00 a.m.
- `watch_wallet.py`: cada 2 minutos
  - **Ojo**: escribe "Sin posiciones nuevas" en cada corrida, o sea ~720
    líneas al día de ruido. Debería registrar solo cuando algo cambia.

## Estado

- Repositorio git con remoto en GitHub, rama `main`.
- **11 commits sin subir** al 16 sep 2026 (`git push`).
- **Sin ninguna prueba automática.** 2,086 líneas que deciden en qué poner
  dinero. Modelo a seguir para empezar: `C:\TradingBot\test_utilidades.py`
  — un módulo sin dependencias pesadas, y cada prueba nombra en su docstring
  el problema real que la provocó.
