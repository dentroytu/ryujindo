#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sirve la web en local para verla como se verá publicada.

    python3 web/servir.py          →  http://localhost:8765

Abrir el `index.html` con doble clic también funciona, pero un servidor se
comporta como el sitio de verdad —rutas, cachés, el `file://` que algunos
navegadores tratan aparte— y es la única forma de que lo que se mira sea lo que
se va a publicar.
"""
import http.server
import os
import socketserver
import sys

# El puerto: primero el argumento, luego `PORT` del entorno —que es como lo
# asigna quien lanza la previa, y evita chocar con una copia ya levantada— y por
# ultimo el 8765 de siempre, que es el que documenta el README.
PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", 8765))

os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Silencioso(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Sin caché: mirando una página que se está retocando, lo peor que puede
        # pasar es estar mirando la de antes sin saberlo.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PUERTO), Silencioso) as httpd:
    print("web servida en http://localhost:%d" % PUERTO, flush=True)
    httpd.serve_forever()
