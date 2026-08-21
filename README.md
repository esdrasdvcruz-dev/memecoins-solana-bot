# Bot de Análisis de Memecoins en Solana

Analiza el mercado de memecoins en Solana todos los días, aplica filtros de
confiabilidad (liquidez, autoridad del token, concentración de holders,
edad, volumen), calcula un score de 0 a 100 por token y envía un reporte
con el top 10 por Telegram.

**Ya está probado end-to-end con datos reales** (DexScreener, Jupiter,
RugCheck, RPC de Solana y envío real por Telegram) durante la construcción
de este proyecto.

## ⚠️ Esto no es asesoría financiera

Los memecoins son extremadamente volátiles y de alto riesgo. Los filtros de
este bot reducen el riesgo de rugs obvios, pero **no garantizan nada**. El
reporte incluye siempre una advertencia de riesgo. Verifica todo por tu
cuenta antes de invertir un solo dólar.

---

## 1. Estructura del proyecto

```
mi-proyecto/
├── bot.py                    # Orquestador principal del reporte diario (python bot.py)
├── watch_wallet.py           # Vigila tu wallet y manda análisis en vivo al abrir una posición
├── dashboard.py               # Genera dashboard.html (mapa de burbujas de tokens evaluados)
├── publish_dashboard.py       # Publica dashboard.html en GitHub Pages (vía deploy key SSH)
├── serve_dashboard.py         # Sirve dashboard.html por WiFi local (para verlo en el celular)
├── abrir_mapa_movil.bat       # Doble clic = corre serve_dashboard.py sin abrir terminal a mano
├── config.py                 # Variables de entorno y umbrales de filtrado
├── scoring.py                # Filtros de confiabilidad + cálculo del score 0-100
├── telegram_report.py        # Formateo y envío del reporte por Telegram
├── data_sources/
│   ├── dexscreener.py        # Descubrimiento de tokens + datos de mercado
│   ├── jupiter.py            # Descubrimiento adicional (recientes/trending/organic score)
│   ├── rugcheck.py           # Score de seguridad, holders, mint/freeze authority
│   ├── solana_rpc.py         # Respaldo vía RPC de Solana si RugCheck no tiene el token
│   └── wallet.py             # Balances de tokens SPL de una wallet (para watch_wallet.py)
├── data/
│   ├── history.json          # Historial local (para calcular momentum de holders)
│   ├── wallet_positions.json # Último snapshot de balances de la wallet vigilada
│   └── bot.log               # Log de cada corrida
├── dashboard.html             # Mapa de burbujas generado (se sobrescribe cada corrida)
├── requirements.txt
├── .env                      # Tus credenciales (NO se sube a git)
├── .env.example               # Plantilla del .env
└── README.md
```

Cada archivo de `data_sources/` y `scoring.py`/`telegram_report.py` se puede
ejecutar solo para probarlo de forma aislada, por ejemplo:

```powershell
python -m data_sources.dexscreener
python -m data_sources.rugcheck
python -m data_sources.solana_rpc
python scoring.py
python telegram_report.py
```

## 2. Requisitos previos

- Python 3.10 o superior instalado y en el PATH (`python --version`).
- Conexión a internet (todas las APIs usadas son gratuitas y no requieren
  API key).
- Una cuenta de Telegram.

## 3. Instalación

Abre PowerShell en la carpeta del proyecto:

```powershell
cd C:\Users\perri\Documents\mi-proyecto
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Si `Activate.ps1` da error de permisos, ejecuta una vez (como usuario
> normal, no hace falta admin):
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## 4. Crear el bot de Telegram con BotFather

1. Abre Telegram y busca el usuario **@BotFather** (tiene la insignia de
   verificado).
2. Envíale el comando `/newbot`.
3. Te pedirá un **nombre** para el bot (puede ser cualquier texto, ej.
   "Mi Memecoin Scanner").
4. Te pedirá un **username** único que debe terminar en `bot` (ej.
   `mi_memecoin_scanner_bot`).
5. BotFather te responde con un mensaje que incluye el **token**, con este
   formato: `123456789:AAHk...................`. Guárdalo, es la contraseña
   de tu bot — no lo compartas ni lo subas a un repositorio público.

## 5. Obtener tu chat ID

1. Busca tu bot recién creado por el username que elegiste y presiona
   **Iniciar / Start** (o mándale cualquier mensaje). Esto es obligatorio:
   un bot no puede escribirle primero a un usuario que nunca le habló.
2. Abre esta URL en el navegador, reemplazando `<TOKEN>` por tu token:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Busca en la respuesta JSON el campo `"chat":{"id":...}` — ese número es
   tu `TELEGRAM_CHAT_ID`.
   - Alternativa más simple: busca el bot **@userinfobot** en Telegram,
     mándale un mensaje, y te devuelve tu ID directamente.
4. Si en vez de a ti quieres que el bot le escriba a un **grupo o canal**,
   agrégalo ahí, mándale un mensaje mencionando al bot, y repite el paso 2:
   el chat ID de un grupo/canal es un número negativo que suele empezar con
   `-100`.

## 6. Configurar el archivo `.env`

Copia la plantilla y edítala:

```powershell
copy .env.example .env
notepad .env
```

Reemplaza:

```
TELEGRAM_BOT_TOKEN=el_token_que_te_dio_botfather
TELEGRAM_CHAT_ID=el_id_que_obtuviste_en_el_paso_anterior
```

Los filtros de confiabilidad (liquidez mínima, holders mínimos, etc.) ya
vienen con los valores pedidos en el diseño del bot; puedes ajustarlos
descomentando las líneas correspondientes en `.env` si algún día quieres
un bot más o menos estricto.

## 7. Ejecutar manualmente

```powershell
python bot.py
```

Vas a ver logs en la consola (y guardados en `data/bot.log`) mientras el
bot descubre tokens, los filtra y calcula el score. Al final, revisa tu
chat de Telegram: si algún token pasó todos los filtros, recibirás un
mensaje de cabecera, un mensaje por cada token del top 10, y un mensaje
final con la advertencia de riesgo. Si ningún token pasó los filtros ese
día, el bot te avisa igual (no se queda en silencio).

**Nota realista:** en el universo de tokens que expone gratis la API de
DexScreener (ver limitaciones abajo), es normal y esperable que muchos días
pasen **menos de 10 tokens** los filtros, o incluso ninguno — eso significa
que los filtros están funcionando, no que el bot esté fallando.

## 8. Cómo funciona el análisis

### Fuentes de datos
- **DexScreener** (`data_sources/dexscreener.py`): descubre tokens nuevos o
  con actividad reciente en Solana y trae precio, market cap, liquidez,
  volumen y antigüedad del par.
- **Jupiter Token API v2** (`data_sources/jupiter.py`): fuente adicional de
  descubrimiento (tokens recientes, trending 24h y con mejor "organic
  score"), gratis y sin API key. Amplía bastante el universo de candidatos
  respecto a usar solo DexScreener (~200+ candidatos en vez de ~50-60).
- **RugCheck** (`data_sources/rugcheck.py`): score de seguridad, si la
  mint/freeze authority están revocadas, holders totales, concentración del
  top 10 de holders (excluyendo las propias cuentas de los pools de
  liquidez) y % de liquidez bloqueada/quemada.
- **RPC de Solana** (`data_sources/solana_rpc.py`): respaldo cuando
  RugCheck todavía no indexó un token (usa `getAccountInfo` para
  mint/freeze authority y `getTokenLargestAccounts` para concentración de
  holders).

### Si algo falla a mitad de la corrida

`bot.py` envuelve todo el análisis en un manejo de errores: si cualquier
paso revienta (una API caída, un bug, etc.), además de quedar el traceback
completo en `data/bot.log`, te llega un mensaje de Telegram avisando que la
corrida de hoy falló, con un extracto del error. Así te enteras sin tener
que ir a revisar el log a mano.

### Filtros de confiabilidad (se descarta el token si falla cualquiera)
| Filtro | Umbral por defecto |
|---|---|
| Liquidez | ≥ $50,000 USD |
| Liquidez bloqueada/quemada | ≥ 80% |
| Mint authority | Revocada |
| Freeze authority | Revocada |
| Top 10 holders | ≤ 30% del supply |
| Edad del par | ≥ 24 horas |
| Holders totales | ≥ 500 |
| Volumen 24h | ≥ $100,000 USD |
| Marcado como "rugged" por RugCheck | Excluido siempre |

### Score (0-100)
- **40% Seguridad**: score de riesgo de RugCheck, invertido (100 = más
  seguro).
- **30% Momentum**: promedio de (a) aceleración del volumen de la última
  hora comparado contra el promedio diario, y (b) crecimiento del número de
  holders desde la corrida anterior del bot (usa `data/history.json` como
  memoria local del día anterior).
- **30% Liquidez**: escala logarítmica entre el mínimo exigido ($50k) y
  $1M de liquidez.

## 9. Mapa de burbujas de tokens (`dashboard.html`)

Cada corrida de `bot.py` genera (o sobrescribe) `dashboard.html` en la raíz
del proyecto: un mapa de burbujas (estilo bubblemaps.io) con **todos** los
candidatos evaluados en esa corrida, hayan pasado o no los filtros de
confiabilidad (no solo el top 10 que se manda por Telegram).

- **Cada burbuja** es un token, con su logo (si DexScreener lo tiene; si
  no, un círculo semitransparente con el símbolo como respaldo automático).
- **Tamaño**: market cap (o liquidez si no hay market cap), en escala
  logarítmica — sin eso, un token grande y establecido (ej. JUP) aplastaría
  a todas las memecoins pequeñas hasta hacerlas invisibles.
- **Anillo de color**: score 0-100, de rojo (riesgoso) a verde (seguro).
- **Anillo sólido** = pasa todos los filtros de confiabilidad; **punteado**
  = no pasa (igual se muestra, para tener panorama completo del mercado
  analizado).
- **Barra superior**: ranking de los 8 tokens con mejor score.
- **Panel "Tokens en tendencia"** (a la derecha, estilo la lista de
  bubblemaps.io): todos los tokens evaluados ordenados por score, con
  logo, cambio 24h y score. Clic en una fila resalta esa burbuja en el
  mapa (mismo mecanismo que el buscador).
- **Buscador**: filtra por nombre/símbolo en vivo (también resalta la fila
  correspondiente en el panel de tendencia).
- **Toggle** "Solo los que pasan los filtros".
- Pasar el mouse por encima de una burbuja muestra precio, market cap,
  liquidez, volumen, holders, seguridad y por qué no pasó los filtros (si
  aplica). Clic abre el token en DexScreener.
- Se autorrefresca sola cada 5 minutos, así que dejarla abierta siempre
  muestra los datos más recientes.

Se sobrescribe en cada corrida diaria (no acumula historial entre días,
solo la foto más reciente).

### Dónde verlo

**En la PC**: doble clic en `dashboard.html` (carpeta del proyecto), o
arrastrándolo a Chrome.

**Desde cualquier lugar (recomendado)**: el bot publica automáticamente
una copia en `https://esdrasdvcruz-dev.github.io/memecoins-solana-bot/`
después de cada corrida (ver "Publicación pública" abajo) — funciona desde
el celular con datos móviles, no hace falta estar en la misma WiFi.

**Desde el celular por WiFi local** (alternativa sin depender de
internet/GitHub): con el celular en la misma red que esta PC, doble clic
en `abrir_mapa_movil.bat` (o `python serve_dashboard.py`) y abre la URL
`http://192.168.x.x:8642/` que muestra la consola. Por seguridad, ese
servidor solo devuelve `dashboard.html` sin importar la ruta pedida, nunca
expone el resto de la carpeta (que incluye `.env`).

### Publicación pública (GitHub Pages) y link en Telegram

Cada mensaje de token que manda el bot por Telegram (reporte diario y
análisis en vivo de `watch_wallet.py`) incluye, junto al link de
DexScreener, un link **"Ver en el mapa de burbujas"** que abre el mapa
público con ese token resaltado automáticamente (usa `?q=SÍMBOLO` en la
URL, que `dashboard.html` lee al cargar).

Para que ese link funcione desde cualquier lugar (no solo en tu WiFi de
casa), `dashboard.html` se publica automáticamente en GitHub Pages después
de cada corrida, vía `publish_dashboard.py`:

1. El repo de GitHub es **público** (GitHub Pages gratis lo requiere) — tu
   `.env` con credenciales nunca se sube porque está en `.gitignore`, así
   que eso queda a salvo igual.
2. Existe una rama `gh-pages` en el repo que solo contiene un `index.html`
   (copia de `dashboard.html`), publicada como sitio en
   `https://esdrasdvcruz-dev.github.io/memecoins-solana-bot/`.
3. `publish_dashboard.py` copia el `dashboard.html` recién generado al
   worktree local `.gh-pages-worktree/index.html`, hace commit y push a
   `gh-pages` — usando una **deploy key SSH dedicada** (solo puede escribir
   en este repo, no tiene acceso al resto de tu cuenta de GitHub) para que
   la tarea programada diaria pueda publicar sin que nadie esté presente
   para pasar un login/token a mano.
4. Si la publicación falla (sin internet, deploy key revocada, etc.) se
   registra en `data/bot.log` pero **no interrumpe** la corrida: el
   reporte de Telegram y el `dashboard.html` local se generan igual.

**Recrear esto desde cero** (otra PC, deploy key revocada, etc.):
```powershell
ssh-keygen -t ed25519 -f ~/.ssh/memecoins_deploy_key -N '""' -C "memecoins-dashboard-deploy"
```
Agrega un bloque a `~/.ssh/config`:
```
Host github-memecoins-deploy
    HostName github.com
    User git
    IdentityFile ~/.ssh/memecoins_deploy_key
    IdentitiesOnly yes
```
Agrega la llave pública (`cat ~/.ssh/memecoins_deploy_key.pub`) como
**Deploy key** en `github.com/<usuario>/<repo>/settings/keys`, marcando
**"Allow write access"**. Luego crea el worktree y el remoto:
```powershell
git worktree add --orphan -b gh-pages .gh-pages-worktree
# copia un dashboard.html generado como .gh-pages-worktree/index.html, luego:
cd .gh-pages-worktree
git add index.html
git commit -m "Publica mapa de burbujas"
git remote add deploy github-memecoins-deploy:<usuario>/<repo>.git
git push deploy gh-pages
```
Y activa GitHub Pages en `settings/pages`: Source = "Deploy from a
branch", Branch = `gh-pages` / `(root)`.

**Probar manualmente**: corre `python bot.py` (o el flujo completo del
`README`) y luego abre `dashboard.html` con doble clic, o `python
publish_dashboard.py` para forzar solo la publicación pública.

## 10. Programar la ejecución diaria a las 8am (Windows)

> **Estado en esta máquina**: la tarea `MemecoinSolanaBot` ya está creada y
> configurada para correr "pase lo que pase":
> - Diaria a las 8:00 am, usando `pythonw.exe` (sin ventana de consola).
> - `LogonType: Password` → corre aunque no hayas iniciado sesión en
>   Windows.
> - `StartWhenAvailable` → si el PC estaba apagado/dormido a las 8am, corre
>   apenas se prenda.
> - `WakeToRun` → despierta el equipo si está dormido (no si está apagado).
> - No se detiene por estar en batería, y tiene un límite de 1 hora por si
>   alguna corrida se cuelga.
>
> Los pasos de abajo son por si necesitas recrearla desde cero (otra PC,
> reinstalación, etc.) o entender qué se configuró.

### Opción A: interfaz gráfica del Programador de tareas

1. Abre el menú Inicio, escribe **"Programador de tareas"** y ábrelo.
2. En el panel derecho, clic en **"Crear tarea básica..."**.
3. **Nombre**: `Memecoin Solana Bot Diario` → Siguiente.
4. **Desencadenador**: `Diariamente` → Siguiente → hora de inicio
   **08:00:00**, repetir cada 1 día → Siguiente.
5. **Acción**: `Iniciar un programa` → Siguiente.
6. **Programa o script**: pega la ruta a `pythonw.exe` (así corre en segundo
   plano sin abrir ninguna ventana):
   ```
   C:\Users\perri\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe
   ```
7. **Agregar argumentos**:
   ```
   C:\Users\perri\Documents\mi-proyecto\bot.py
   ```
8. **Iniciar en (opcional)**:
   ```
   C:\Users\perri\Documents\mi-proyecto
   ```
9. Siguiente → Finalizar.
10. Busca la tarea recién creada en la lista, clic derecho →
    **Propiedades**. En la pestaña **General**, marca *"Ejecutar tanto si
    el usuario inició sesión como si no"* si quieres que corra aunque no
    hayas iniciado sesión en Windows a esa hora (te pedirá tu contraseña de
    Windows una vez para guardarlo).
11. En la pestaña **Condiciones**, si usas laptop, puedes desmarcar
    *"Iniciar la tarea solo si el equipo está conectado a la corriente"*.

Para confirmar que quedó bien configurada, selecciónala en la lista y haz
clic en **"Ejecutar"** — revisa tu Telegram y el archivo `data/bot.log`.

### Opción B: una sola línea en PowerShell (`schtasks`)

Alternativa más rápida a los pasos de arriba, ejecutada una sola vez en
PowerShell (no necesita permisos de administrador):

```powershell
schtasks /Create /TN "MemecoinSolanaBot" /TR "\"C:\Users\perri\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe\" \"C:\Users\perri\Documents\mi-proyecto\bot.py\"" /SC DAILY /ST 08:00
```

Para probarla manualmente sin esperar a las 8am:

```powershell
schtasks /Run /TN "MemecoinSolanaBot"
```

Para que corra "pase lo que pase" (recuperarse si el PC estaba apagado o
dormido, no detenerse por batería, etc.), aplica esto una vez con el
módulo `ScheduledTasks` de PowerShell:

```powershell
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -WakeToRun `
    -DontStopOnIdleEnd `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Set-ScheduledTask -TaskName "MemecoinSolanaBot" -Settings $settings
```

Y para que corra aunque no hayas iniciado sesión en Windows, ese paso sí
requiere tu contraseña y **no se puede hacer por línea de comandos de forma
no interactiva de manera segura** — hazlo desde la interfaz gráfica: clic
derecho sobre la tarea → Propiedades → pestaña General → marca *"Ejecutar
tanto si el usuario inició sesión como si no"* → Aceptar → escribe tu
contraseña de Windows cuando te la pida.

Para eliminarla si algún día ya no la quieres:

```powershell
schtasks /Delete /TN "MemecoinSolanaBot" /F
```

## 11. Análisis en vivo al abrir una posición (`watch_wallet.py`)

Axiom (y la mayoría de terminales de trading) no tiene una API pública para
leer tus posiciones abiertas. En vez de integrarse con Axiom, `watch_wallet.py`
vigila directamente tu wallet de Solana on-chain: cada vez que compras un
token, éste queda en tu wallet, así que monitorear la wallet es más
confiable.

**Cómo funciona:**
1. Cada 2 minutos (tarea programada `MemecoinWalletWatch`) revisa los
   balances de tokens de tu wallet (`WALLET_ADDRESS` en `.env`) vía RPC de
   Solana.
2. Compara contra el último snapshot guardado en
   `data/wallet_positions.json`. Cualquier token con balance > 0 que antes
   estaba en 0 (o no existía) se trata como posición nueva.
3. Corre el mismo análisis del reporte diario (DexScreener + RugCheck/RPC +
   score) sobre ese token y te lo manda por Telegram al instante — **sin**
   descartarlo aunque no pase los filtros de confiabilidad (la posición ya
   está abierta, así que se informa igual, marcando qué filtros no pasaría).
4. Avisa **una sola vez** por posición: mientras el token siga en la
   wallet no se vuelve a avisar. Si lo vendes por completo (balance a 0) y
   lo vuelves a comprar después, se vuelve a tratar como posición nueva.

La primera vez que corre, guarda tus tenencias actuales como línea base
**sin avisar** (para no notificar de posiciones que ya tenías antes de
activar esta función).

**Configurar `WALLET_ADDRESS`**: agrega en `.env` la dirección **pública**
de tu wallet (nunca la clave privada ni el seed phrase):
```
WALLET_ADDRESS=tu_direccion_publica_de_solana
```

**Probar manualmente:**
```powershell
python watch_wallet.py
```

**Tarea programada** (ya configurada en esta máquina, `MemecoinWalletWatch`,
cada 2 minutos, `pythonw.exe` sin ventana). Para recrearla desde cero:
```powershell
schtasks /Create /TN "MemecoinWalletWatch" /TR "\"C:\Users\perri\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe\" \"C:\Users\perri\Documents\mi-proyecto\watch_wallet.py\"" /SC MINUTE /MO 2 /ST 00:00
```
```powershell
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

Set-ScheduledTask -TaskName "MemecoinWalletWatch" -Settings $settings
```
Para eliminarla: `schtasks /Delete /TN "MemecoinWalletWatch" /F`

## 12. Limitaciones conocidas (léelas antes de confiar ciegamente en el bot)

- **Universo de descubrimiento limitado**: DexScreener no ofrece un
  endpoint gratuito que liste "todos los pares nuevos de Solana". El bot
  combina `/token-profiles/latest/v1` y `/token-boosts/latest/v1|top/v1`
  para descubrir candidatos, que en la práctica son sobre todo tokens con
  perfil cargado o boosteados recientemente. Esto significa que puede haber
  memecoins legítimos que el bot nunca llega a evaluar. Si en el futuro
  quieres ampliar la cobertura, se puede añadir una lista de tokens
  semilla o una API de pago con endpoint de "nuevos pares".
- **Solscan público está descontinuado**: `public-api.solscan.io` ya
  devuelve 404; Solscan ahora exige API key de pago en `pro-api.solscan.io`.
  Por eso el respaldo de holders usa el RPC público de Solana en su lugar.
- **RPC público de Solana limita `getTokenLargestAccounts`**: el nodo
  público (`api.mainnet-beta.solana.com`) devuelve 429 con frecuencia en
  ese método. El bot reintenta con backoff, pero si sigue fallando, el
  token se descarta por falta de datos en vez de asumir que es seguro.
- **RugCheck limita ~15 requests/minuto**: por eso el bot primero
  preselecciona candidatos con datos baratos de DexScreener (liquidez,
  volumen, edad) antes de gastar ese cupo consultando seguridad.
- **"Momentum de holders" necesita al menos 2 corridas**: la primera vez
  que un token aparece, no hay dato del día anterior, así que ese
  componente del score queda neutral (50/100) hasta la segunda corrida.

## 13. Solución de problemas

- **"Faltan TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID en .env"**: revisa que el
  archivo se llame exactamente `.env` (no `.env.txt`) y esté en la raíz del
  proyecto.
- **No llega ningún mensaje pero el log no muestra error**: confirma que le
  diste "Start" a tu bot al menos una vez (paso 5) y que el `chat_id` es
  correcto.
- **La tarea programada no genera log ni manda mensajes**: revisa
  `data/bot.log`; si no se crea el archivo, la tarea probablemente no está
  encontrando `bot.py` — verifica las rutas exactas en el paso 9.
- **Quieres ver qué tokens se descartaron y por qué**: todos los motivos de
  descarte se registran en `data/bot.log` (nivel INFO), token por token.
- **`watch_wallet.py` no detecta una posición nueva**: revisa que
  `WALLET_ADDRESS` en `.env` sea la dirección correcta y que la compra ya
  se haya confirmado on-chain (puede tardar unos segundos). También
  confirma en `data/bot.log` que la tarea `MemecoinWalletWatch` esté
  corriendo cada 2 minutos.
