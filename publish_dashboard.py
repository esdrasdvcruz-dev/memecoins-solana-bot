"""
Publica dashboard.html en GitHub Pages (rama gh-pages) para que el link
que se manda por Telegram funcione desde cualquier lugar, no solo en la
red local.

Usa una llave SSH dedicada (deploy key de SOLO escritura en este repo,
sin acceso al resto de la cuenta de GitHub, configurada en ~/.ssh/config
bajo el host "github-memecoins-deploy") para poder hacer push sin
intervención manual desde la tarea programada diaria — así se evita que
Git Credential Manager se cuelgue pidiendo login por HTTPS en un proceso
sin sesión interactiva (ver memoria del proyecto sobre este problema).

Requiere que exista el worktree local `.gh-pages-worktree` (rama
gh-pages) con el remoto `deploy` ya configurado — se creó una sola vez a
mano durante la configuración inicial, este módulo no lo crea.

Si la publicación falla (sin internet, deploy key revocada, etc.) se
registra en el log pero NO interrumpe la corrida diaria: el reporte de
Telegram y el dashboard.html local igual se generan con normalidad.
"""

from __future__ import annotations

import logging
import subprocess

import config

logger = logging.getLogger(__name__)

WORKTREE = config.BASE_DIR / ".gh-pages-worktree"
REMOTE = "deploy"
BRANCH = "gh-pages"


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(WORKTREE), *args],
        capture_output=True,
        text=True,
        timeout=60,
    )


def publish_dashboard() -> bool:
    """Copia dashboard.html al worktree de gh-pages y lo publica si hay
    cambios. Devuelve True si se publicó, False si no había nada nuevo o
    si algo falló (el detalle queda registrado en el log)."""
    if not WORKTREE.exists():
        logger.warning(
            "No existe %s (worktree de gh-pages), se omite la publicación pública", WORKTREE
        )
        return False

    (WORKTREE / "index.html").write_bytes(config.DASHBOARD_FILE.read_bytes())

    add = _git("add", "index.html")
    if add.returncode != 0:
        logger.warning("git add falló al publicar el dashboard: %s", add.stderr.strip())
        return False

    diff = _git("diff", "--cached", "--quiet")
    if diff.returncode == 0:
        logger.info("Dashboard público sin cambios, no se vuelve a publicar")
        return False

    commit = _git("commit", "-m", "Actualiza mapa de burbujas")
    if commit.returncode != 0:
        logger.warning("git commit falló al publicar el dashboard: %s", commit.stderr.strip())
        return False

    push = _git("push", REMOTE, BRANCH)
    if push.returncode != 0:
        logger.warning("git push falló al publicar el dashboard: %s", push.stderr.strip())
        return False

    logger.info("Dashboard publicado en %s", config.PUBLIC_DASHBOARD_URL)
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    published = publish_dashboard()
    print("Publicado" if published else "Sin cambios / no publicado (ver log)")
