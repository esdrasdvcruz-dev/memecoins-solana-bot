"""
Genera dashboard.html: un mapa de burbujas (circle packing) de todos los
tokens evaluados en la última corrida del bot, pasen o no los filtros de
confiabilidad.

  - Tamaño de cada burbuja: market cap (o liquidez si no hay market cap),
    en escala logarítmica (si no, un token grande y establecido aplasta
    visualmente a las memecoins pequeñas).
  - Cada burbuja muestra el logo del token (si DexScreener lo tiene) con
    un anillo de color según el score 0-100 (rojo = riesgoso, verde =
    seguro). Sin logo disponible, muestra el símbolo sobre un círculo del
    color del score.
  - Anillo sólido = pasa todos los filtros; punteado = no pasa.
  - Barra superior con el top 8 por score, buscador para filtrar por
    nombre/símbolo, y toggle para ver solo los que pasan los filtros.
  - Clic en una burbuja abre el token en DexScreener.

Es un archivo HTML autocontenido (los datos van embebidos como JSON) para
poder abrirlo con doble clic sin depender de un servidor local; usa D3.js
desde CDN solo para el layout (`d3.pack`), así que necesita conexión a
internet para cargarlo (el bot ya requiere internet para analizar, así que
en la práctica siempre hay conexión disponible cuando se genera/abre). Los
logos también se cargan desde el CDN de DexScreener; si una imagen no
carga, se usa el círculo de color + símbolo como respaldo automático.

Se regenera en cada corrida de bot.py, sobrescribiendo el archivo anterior
(no acumula historial entre días, solo muestra la foto más reciente).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_FIELDS = (
    "address",
    "name",
    "symbol",
    "url",
    "image_url",
    "price_usd",
    "market_cap",
    "liquidity_usd",
    "volume_24h",
    "price_change_24h",
    "total_holders",
    "top10_holder_pct",
    "lp_locked_pct",
    "score",
    "passed",
    "fail_reasons",
)


def _dashboard_token(token: dict) -> dict:
    row = {field: token.get(field) for field in _FIELDS}
    row["security_score"] = (token.get("score_breakdown") or {}).get("security")
    if not row.get("url"):
        row["url"] = f"https://dexscreener.com/solana/{token.get('pair_address', token.get('address'))}"
    return row


def _embeddable_json(data: object) -> str:
    """JSON para incrustar dentro de un <script>: escapa '</' para que un
    nombre/símbolo de token malicioso (ej. contiene '</script>') no pueda
    cortar el tag y ejecutar HTML/JS arbitrario en la página."""
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


_TEMPLATE = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Mapa de burbujas - Memecoins Solana</title>
<meta http-equiv="refresh" content="300">
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    height: 100%;
    background: #05060a;
    color: #e7e9ee;
    font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
  }
  body {
    background:
      radial-gradient(ellipse 900px 500px at 15% -10%, rgba(124,58,237,0.35), transparent 60%),
      radial-gradient(ellipse 900px 600px at 110% 10%, rgba(16,185,129,0.18), transparent 55%),
      #05060a;
  }
  header {
    padding: 18px 24px 10px;
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
  }
  header h1 {
    font-size: 19px;
    margin: 0;
    font-weight: 700;
    letter-spacing: 0.2px;
  }
  header .meta { color: #8b90a0; font-size: 12.5px; }

  #ranking {
    display: flex;
    gap: 8px;
    padding: 0 24px 14px;
    overflow-x: auto;
  }
  .chip {
    display: flex;
    align-items: center;
    gap: 6px;
    background: #12141e;
    border: 1px solid #23273a;
    border-radius: 999px;
    padding: 5px 12px 5px 6px;
    white-space: nowrap;
    font-size: 12px;
    flex: 0 0 auto;
  }
  .chip img, .chip .fallback {
    width: 20px; height: 20px; border-radius: 50%; object-fit: cover;
    background: #23273a;
  }
  .chip .fallback {
    display: flex; align-items: center; justify-content: center;
    font-size: 9px; font-weight: 700; color: #cfd3de;
  }
  .chip .rank { color: #6c7185; font-weight: 600; }
  .chip .score { color: #8b90a0; }

  #controls {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 4px 24px 14px;
    flex-wrap: wrap;
  }
  #search {
    background: #10121b;
    border: 1px solid #262a3a;
    border-radius: 999px;
    padding: 9px 16px;
    color: #e7e9ee;
    font-size: 13px;
    width: 260px;
    outline: none;
  }
  #search:focus { border-color: #7c3aed; }
  .toggle {
    display: flex; align-items: center; gap: 6px;
    font-size: 12.5px; color: #b6bacb; cursor: pointer; user-select: none;
  }
  .legend {
    display: flex; align-items: center; gap: 12px;
    font-size: 11.5px; color: #8b90a0; margin-left: auto; flex-wrap: wrap;
  }
  .legend .grad {
    width: 130px; height: 8px; border-radius: 4px;
    background: linear-gradient(to right, #d73027, #fee08b, #1a9850);
  }
  .legend .swatch { display: inline-flex; align-items: center; gap: 6px; }
  .legend .ring { width: 11px; height: 11px; border-radius: 50%; }

  #main-area { display: flex; gap: 14px; padding: 4px 12px 20px; align-items: flex-start; }
  #chart-wrap { flex: 1; min-width: 0; }
  svg { width: 100%; height: 78vh; display: block; }

  #list-panel {
    width: 320px;
    flex-shrink: 0;
    background: #0d0f18;
    border: 1px solid #1c2030;
    border-radius: 14px;
    max-height: 78vh;
    overflow-y: auto;
  }
  #list-panel h2 {
    font-size: 12.5px;
    margin: 0;
    padding: 12px 14px;
    color: #8b90a0;
    font-weight: 600;
    border-bottom: 1px solid #1c2030;
    position: sticky;
    top: 0;
    background: #0d0f18;
  }
  .list-row {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 8px 14px;
    cursor: pointer;
    border-bottom: 1px solid #14161f;
  }
  .list-row:hover, .list-row.active { background: #151827; }
  .list-row img, .list-row .fallback {
    width: 26px; height: 26px; border-radius: 50%; object-fit: cover; background: #23273a; flex-shrink: 0;
  }
  .list-row .fallback { display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: 700; }
  .list-row .names { flex: 1; min-width: 0; }
  .list-row .sym { font-weight: 700; font-size: 12.5px; color: #f4f5f7; }
  .list-row .nm { font-size: 10.5px; color: #6c7185; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .list-row .chg { font-size: 11.5px; width: 54px; text-align: right; flex-shrink: 0; }
  .list-row .chg.up { color: #51cf66; }
  .list-row .chg.down { color: #ff6b6b; }
  .list-row .scorepill {
    font-size: 10.5px; font-weight: 700; border-radius: 999px; padding: 2px 7px; flex-shrink: 0;
  }
  .bubble { cursor: pointer; }
  .bubble .bg { filter: blur(0.4px); }
  .bubble .ring.passed { stroke-width: 2.2px; }
  .bubble .ring.failed { stroke-dasharray: 3 3; stroke-width: 2px; }
  .bubble text {
    fill: #f4f5f7;
    text-anchor: middle;
    font-weight: 700;
    pointer-events: none;
    paint-order: stroke;
    stroke: #05060a;
    stroke-width: 3px;
  }
  .bubble .sub { fill: #cfd3de; font-weight: 500; }
  .bubble.dim { opacity: 0.12; }

  #tooltip {
    position: fixed;
    pointer-events: none;
    background: #0f111a;
    border: 1px solid #262a3a;
    border-radius: 12px;
    padding: 0;
    font-size: 12.5px;
    line-height: 1.5;
    width: 280px;
    display: none;
    z-index: 10;
    box-shadow: 0 12px 32px rgba(0,0,0,0.55);
    overflow: hidden;
  }
  #tooltip .th {
    display: flex; align-items: center; gap: 10px;
    padding: 12px 14px; background: #151827;
  }
  #tooltip .th img, #tooltip .th .fallback {
    width: 34px; height: 34px; border-radius: 50%; object-fit: cover; background: #23273a;
  }
  #tooltip .th .fallback { display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; }
  #tooltip .name { font-weight: 700; color: #fff; font-size: 13.5px; }
  #tooltip .score-badge { margin-left: auto; font-weight: 700; }
  #tooltip .body { padding: 10px 14px 12px; }
  #tooltip .row { display: flex; justify-content: space-between; color: #b6bacb; margin: 2px 0; }
  #tooltip .row b { color: #e7e9ee; font-weight: 600; }
  #tooltip .risk { color: #ff6b6b; margin-top: 6px; }
  #tooltip .ok { color: #51cf66; margin-top: 6px; }
  #tooltip .hint { color: #6c7185; margin-top: 6px; font-size: 11px; }

  #empty { padding: 60px 20px; text-align: center; color: #8b90a0; }
</style>
</head>
<body>
<header>
  <h1>&#129749; Mapa de burbujas &mdash; Memecoins Solana</h1>
  <span class="meta">{{GENERATED_AT}} &middot; {{TOTAL}} tokens evaluados &middot; {{PASSED}} pasaron los filtros &middot; se actualiza sola cada 5 min</span>
</header>
<div id="ranking"></div>
<div id="controls">
  <input id="search" type="text" placeholder="Buscar por nombre o símbolo...">
  <label class="toggle"><input id="onlyPassed" type="checkbox"> Solo los que pasan los filtros</label>
  <div class="legend">
    <span class="swatch">Riesgoso <span class="grad"></span> Seguro</span>
    <span class="swatch"><span class="ring" style="border:2px solid #fff;"></span> Pasa filtros</span>
    <span class="swatch"><span class="ring" style="border:2px dashed #fff;"></span> No pasa</span>
  </div>
</div>
<div id="main-area">
  <div id="chart-wrap"><svg id="chart" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid meet"></svg></div>
  <div id="list-panel">
    <h2>Tokens en tendencia (por score)</h2>
    <div id="list-body"></div>
  </div>
</div>
<div id="empty" style="display:none">Ningún token fue evaluado en la última corrida.</div>
<div id="tooltip"></div>
<script>
const TOKENS = {{TOKENS_JSON}};

function fmtUsd(v) {
  if (v === null || v === undefined) return "N/D";
  if (v >= 1000) return "$" + Math.round(v).toLocaleString("es");
  return "$" + v.toFixed(2);
}
function initials(t) {
  return (t.symbol || t.name || "?").slice(0, 3).toUpperCase();
}
const color = d3.scaleLinear().domain([0, 50, 100]).range(["#d73027", "#fee08b", "#1a9850"]).clamp(true);

// --- Barra de ranking (top 8 por score) ---
const ranking = document.getElementById("ranking");
[...TOKENS].sort((a, b) => (b.score ?? -1) - (a.score ?? -1)).slice(0, 8).forEach((t, i) => {
  const chip = document.createElement("div");
  chip.className = "chip";
  const img = t.image_url
    ? `<img src="${t.image_url}" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'fallback',textContent:'${initials(t)}',style:'color:${color(t.score ?? 0)}'}))">`
    : `<div class="fallback" style="color:${color(t.score ?? 0)}">${initials(t)}</div>`;
  chip.innerHTML = `<span class="rank">#${i + 1}</span>${img}<b>${t.symbol || "?"}</b><span class="score">${t.score ?? "N/D"}</span>`;
  ranking.appendChild(chip);
});

// --- Mapa de burbujas ---
const svg = d3.select("#chart");
const W = 1600, H = 900;

if (!TOKENS.length) {
  document.getElementById("empty").style.display = "block";
  document.getElementById("main-area").style.display = "none";
} else {
  // Escala logarítmica: el market cap de memecoins tiene disparidad extrema
  // (un token establecido puede tener 1000-10000x el cap de uno recién
  // lanzado), así que un tamaño lineal deja casi todo el mapa aplastado en
  // una esquina. El log10 comprime ese rango a algo legible sin perder el
  // orden relativo.
  const root = d3.hierarchy({ children: TOKENS })
    .sum(d => Math.log10((d.market_cap || d.liquidity_usd || 0) + 1000))
    .sort((a, b) => b.value - a.value);

  d3.pack().size([W, H]).padding(5)(root);
  const leaves = root.leaves();

  const tooltip = d3.select("#tooltip");

  const cell = svg.selectAll("g")
    .data(leaves)
    .join("g")
    .attr("class", "bubble")
    .attr("transform", d => `translate(${d.x},${d.y})`)
    .on("mousemove", (event, d) => {
      const t = d.data;
      const img = t.image_url
        ? `<img src="${t.image_url}" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'fallback',textContent:'${initials(t)}'}))">`
        : `<div class="fallback">${initials(t)}</div>`;
      const risks = (t.fail_reasons && t.fail_reasons.length)
        ? `<div class="risk">No pasa: ${t.fail_reasons.join("; ")}</div>`
        : `<div class="ok">Pasa todos los filtros</div>`;
      tooltip
        .style("display", "block")
        .style("left", Math.min(event.clientX + 16, window.innerWidth - 300) + "px")
        .style("top", Math.min(event.clientY + 16, window.innerHeight - 260) + "px")
        .html(
          `<div class="th">${img}<div><div class="name">${t.name || "?"} (${t.symbol || "?"})</div></div>` +
          `<div class="score-badge" style="color:${color(t.score ?? 0)}">${t.score ?? "N/D"}/100</div></div>` +
          `<div class="body">` +
          `<div class="row"><span>Precio</span><b>${t.price_usd ? "$" + t.price_usd : "N/D"}</b></div>` +
          `<div class="row"><span>Cambio 24h</span><b>${t.price_change_24h?.toFixed(1) ?? "N/D"}%</b></div>` +
          `<div class="row"><span>Market Cap</span><b>${fmtUsd(t.market_cap)}</b></div>` +
          `<div class="row"><span>Liquidez</span><b>${fmtUsd(t.liquidity_usd)}</b></div>` +
          `<div class="row"><span>Volumen 24h</span><b>${fmtUsd(t.volume_24h)}</b></div>` +
          `<div class="row"><span>Holders</span><b>${t.total_holders ?? "N/D"}</b></div>` +
          `<div class="row"><span>Seguridad</span><b>${t.security_score ?? "N/D"}/100</b></div>` +
          `<div class="row"><span>Top10 holders / LP bloqueada</span><b>${t.top10_holder_pct ?? "N/D"}% / ${t.lp_locked_pct ?? "N/D"}%</b></div>` +
          risks +
          `<div class="hint">Clic para ver en DexScreener</div>` +
          `</div>`
        );
    })
    .on("mouseleave", () => tooltip.style("display", "none"))
    .on("click", (event, d) => window.open(d.data.url, "_blank", "noopener"));

  cell.append("circle")
    .attr("class", "bg")
    .attr("r", d => d.r)
    .attr("fill", d => color(d.data.score ?? 0))
    .attr("fill-opacity", d => d.data.image_url ? 0.35 : 0.55);

  cell.each(function (d) {
    const t = d.data;
    if (!t.image_url) return;
    const g = d3.select(this);
    const clipId = "clip-" + d.data.address;
    g.append("clipPath").attr("id", clipId).append("circle").attr("r", d.r);
    g.append("image")
      .attr("href", t.image_url)
      .attr("x", -d.r).attr("y", -d.r)
      .attr("width", d.r * 2).attr("height", d.r * 2)
      .attr("preserveAspectRatio", "xMidYMid slice")
      .attr("clip-path", `url(#${clipId})`)
      .on("error", function () { d3.select(this).remove(); });
  });

  cell.append("circle")
    .attr("class", d => "ring " + (d.data.passed ? "passed" : "failed"))
    .attr("r", d => d.r)
    .attr("fill", "none")
    .attr("stroke", d => color(d.data.score ?? 0));

  cell.each(function (d) {
    if (d.data.image_url || d.r < 16) return;
    const g = d3.select(this);
    g.append("text").attr("class", "sym").attr("y", 4).style("font-size", Math.min(d.r * 0.4, 15) + "px").text(d.data.symbol || "?");
  });

  // --- Panel de tokens en tendencia (estilo bubblemaps.io) ---
  const listBody = document.getElementById("list-body");
  const rowByAddress = new Map();
  [...TOKENS].sort((a, b) => (b.score ?? -1) - (a.score ?? -1)).forEach(t => {
    const row = document.createElement("div");
    row.className = "list-row";
    const img = t.image_url
      ? `<img src="${t.image_url}" onerror="this.replaceWith(Object.assign(document.createElement('div'),{className:'fallback',textContent:'${initials(t)}'}))">`
      : `<div class="fallback">${initials(t)}</div>`;
    const chg = t.price_change_24h;
    const chgClass = chg > 0 ? "up" : chg < 0 ? "down" : "";
    row.innerHTML =
      img +
      `<div class="names"><div class="sym">${t.symbol || "?"}</div><div class="nm">${t.name || ""}</div></div>` +
      `<div class="chg ${chgClass}">${chg?.toFixed(1) ?? "N/D"}%</div>` +
      `<div class="scorepill" style="color:${color(t.score ?? 0)};background:${color(t.score ?? 0)}22">${t.score ?? "N/D"}</div>`;
    row.addEventListener("click", () => {
      searchInput.value = t.symbol || t.name || "";
      applyFilters();
    });
    listBody.appendChild(row);
    rowByAddress.set(t.address, row);
  });

  // --- Buscador + toggle "solo pasan filtros" ---
  const searchInput = document.getElementById("search");
  const onlyPassed = document.getElementById("onlyPassed");
  function applyFilters() {
    const q = searchInput.value.trim().toLowerCase();
    cell.classed("dim", d => {
      const t = d.data;
      const matchesSearch = !q || (t.symbol || "").toLowerCase().includes(q) || (t.name || "").toLowerCase().includes(q);
      const matchesFilter = !onlyPassed.checked || t.passed;
      return !(matchesSearch && matchesFilter);
    });
    rowByAddress.forEach((row, addr) => {
      const t = TOKENS.find(x => x.address === addr);
      const matchesSearch = !q || (t.symbol || "").toLowerCase().includes(q) || (t.name || "").toLowerCase().includes(q);
      row.classList.toggle("active", !!q && matchesSearch);
    });
  }
  searchInput.addEventListener("input", applyFilters);
  onlyPassed.addEventListener("change", applyFilters);

  // --- Deep link desde Telegram: ?q=SYMBOL resalta ese token al abrir ---
  const initialQuery = new URLSearchParams(location.search).get("q");
  if (initialQuery) {
    searchInput.value = initialQuery;
    applyFilters();
  }
}
</script>
</body>
</html>
"""


def render_dashboard(evaluated_tokens: list[dict], output_path: Path) -> None:
    rows = [_dashboard_token(t) for t in evaluated_tokens]
    passed_count = sum(1 for t in rows if t.get("passed"))
    generated_at = datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y %H:%M")

    html = (
        _TEMPLATE.replace("{{TOKENS_JSON}}", _embeddable_json(rows))
        .replace("{{GENERATED_AT}}", generated_at)
        .replace("{{TOTAL}}", str(len(rows)))
        .replace("{{PASSED}}", str(passed_count))
    )

    output_path.write_text(html, encoding="utf-8")
    logger.info("Dashboard generado en %s (%d tokens, %d pasaron filtros)", output_path, len(rows), passed_count)


if __name__ == "__main__":
    import config

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    fake_tokens = [
        {
            "address": "ExAmPLE111111111111111111111111111111111",
            "name": "Example Token",
            "symbol": "EXM",
            "url": "https://dexscreener.com/solana/example",
            "image_url": None,
            "price_usd": 0.00001234,
            "market_cap": 1_200_000,
            "liquidity_usd": 150_000,
            "volume_24h": 400_000,
            "price_change_24h": 12.5,
            "total_holders": 1234,
            "top10_holder_pct": 18.2,
            "lp_locked_pct": 100,
            "score": 78,
            "score_breakdown": {"security": 85, "momentum": 60, "liquidity": 90},
            "passed": True,
            "fail_reasons": [],
        },
        {
            "address": "RiSkY2222222222222222222222222222222222222",
            "name": "Risky One",
            "symbol": "RISK",
            "url": "https://dexscreener.com/solana/risky",
            "image_url": None,
            "price_usd": 0.0000007,
            "market_cap": 300_000,
            "liquidity_usd": 20_000,
            "volume_24h": 50_000,
            "price_change_24h": -30.2,
            "total_holders": 120,
            "top10_holder_pct": 55.0,
            "lp_locked_pct": 10,
            "score": 22,
            "score_breakdown": {"security": 15, "momentum": 30, "liquidity": 20},
            "passed": False,
            "fail_reasons": ["liquidez $20,000 < $50,000", "top 10 holders 55.0% > 30%"],
        },
    ]
    render_dashboard(fake_tokens, config.DASHBOARD_FILE)
    print(f"Vista previa generada en {config.DASHBOARD_FILE}")
