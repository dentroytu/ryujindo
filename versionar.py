#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Le pone su versión a la hoja de estilo y al JavaScript.

**Para qué.** GitHub Pages sirve los ficheros con `cache-control: max-age=600`.
Al publicar un cambio, durante diez minutos un navegador que ya haya estado
aquí puede quedarse con el **CSS de antes y el HTML de ahora** — y esa mezcla
es peor que cualquiera de las dos versiones por separado: pasó justo con este
proyecto, con el HTML nuevo diciendo `height="619"` y el CSS viejo sin su
`height: auto`, y la galería entera salió estirada en vertical. Nadie lo ve
venir porque en local no hay caché y en el servidor la página es correcta.

La cura es que la URL cambie cuando cambia el fichero: `estilo.css?v=8f3a1c`,
donde eso es un resumen del propio contenido. El navegador no puede servir de
su caché algo que nunca ha pedido.

**Cómo se usa:**

    python3 versionar.py          # reescribe los enlaces de las dos páginas
    python3 versionar.py --seco   # solo dice si están al día

`comprobar.py` lo verifica, así que publicar con las versiones viejas no se
puede olvidar: la comprobación falla antes.
"""
import hashlib
import io
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PAGINAS = ["index.html", os.path.join("en", "index.html")]
CON_VERSION = ["css/fuentes.css", "css/estilo.css", "js/novedades.js", "js/web.js"]


def sello(rel):
    """Seis caracteres del resumen del fichero. Cambia el fichero, cambia la URL."""
    with io.open(os.path.join(AQUI, rel), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:6]


def main():
    seco = "--seco" in sys.argv
    sellos = {rel: sello(rel) for rel in CON_VERSION}
    desfasados = []

    for pagina in PAGINAS:
        p = os.path.join(AQUI, pagina)
        s = io.open(p, encoding="utf-8").read()
        original = s
        for rel, v in sellos.items():
            # el enlace desde en/ lleva ../ delante
            for pre in ("", "../"):
                s = re.sub(r'(["\'])' + re.escape(pre + rel) + r'(\?v=[0-9a-f]+)?\1',
                           lambda m, p=pre, r=rel, v=v: '%s%s%s?v=%s%s'
                           % (m.group(1), p, r, v, m.group(1)),
                           s)
        if s != original:
            desfasados.append(pagina)
            if not seco:
                io.open(p, "w", encoding="utf-8").write(s)

    for rel, v in sellos.items():
        print("  %-20s v=%s" % (rel, v))

    if desfasados:
        if seco:
            print("\nsin actualizar: " + ", ".join(desfasados))
            sys.exit(1)
        print("\nactualizadas: " + ", ".join(desfasados))
    else:
        print("\ntodo al día.")


if __name__ == "__main__":
    main()
