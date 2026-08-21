"""
Sirve dashboard.html por HTTP en tu red local, para poder abrirlo desde el
celular sin copiar el archivo a mano (con el celular en la MISMA red WiFi
que esta PC).

Por seguridad, este servidor SOLO devuelve el contenido de dashboard.html
sin importar la ruta pedida — nunca lista ni sirve el resto de la carpeta
del proyecto (que incluye `.env` con tus credenciales de Telegram). Cada
request lee el archivo de nuevo, así que siempre muestra la última versión
generada por bot.py.

Uso: python serve_dashboard.py (o doble clic en abrir_mapa_movil.bat)
Deja la ventana abierta mientras quieras poder verlo desde el celular;
ciérrala (o Ctrl+C) para apagar el servidor.

La primera vez que corre, Windows puede preguntar si permite que Python
reciba conexiones en la red — hay que aceptar (marca solo "redes
privadas") para que el celular pueda conectarse.
"""

from __future__ import annotations

import http.server
import socket

import config

PORT = 8642


class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if not config.DASHBOARD_FILE.exists():
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("dashboard.html no existe todavía. Corre bot.py primero.".encode("utf-8"))
            return

        content = config.DASHBOARD_FILE.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args) -> None:  # silencia el log verboso por request
        pass


def _lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def main() -> None:
    with http.server.HTTPServer(("0.0.0.0", PORT), DashboardHandler) as httpd:
        print(f"Sirviendo dashboard.html en el puerto {PORT}")
        print(f"Desde el celular (misma WiFi): http://{_lan_ip()}:{PORT}/")
        print("Ctrl+C (o cierra esta ventana) para detener.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")


if __name__ == "__main__":
    main()
