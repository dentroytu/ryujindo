#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprueba la web antes de subirla.

**Para qué.** Una web de dos idiomas se rompe por sitios que no dan error: una
imagen que se referencia y no está sale como un icono roto, un ancla que apunta
a una sección renombrada no lleva a ninguna parte, y —el peor de los tres— una
lengua que se queda atrás cuando se añade algo a la otra. Ninguna de las tres
cosas la canta el navegador, y las tres se ven mirando la página… si a uno se le
ocurre mirar esa parte.

**Cómo se usa:**

    python3 web/comprobar.py

Devuelve 1 si algo falla, para poder encadenarlo. Se estrenó rompiendo las
cuatro comprobaciones a propósito: una que no ha fallado nunca no prueba nada.
"""
import io
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PAGINAS = [("es", "index.html"), ("en", os.path.join("en", "index.html"))]

fallos = []


def leer(rel):
    with io.open(os.path.join(AQUI, rel), encoding="utf-8") as f:
        return f.read()


def sin_comentarios(js):
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    return re.sub(r"^\s*//.*$", "", js, flags=re.M)


def fallo(que):
    fallos.append(que)


# ── 1 · Todo lo que se referencia existe ────────────────────────────────────
#
# Se resuelve la ruta como la resolvería el navegador: relativa al HTML que la
# escribe, que es la parte que cambia entre index.html y en/index.html y por
# tanto la que se rompe al copiar una página de un idioma a otro.

for lang, pagina in PAGINAS:
    html = leer(pagina)
    base = os.path.dirname(os.path.join(AQUI, pagina))
    refs = re.findall(r'(?:src|href)="([^"#][^"]*)"', html)
    for ref in refs:
        if ref.startswith(("http://", "https://", "mailto:", "data:")):
            continue
        ref = ref.split("?")[0]        # el ?v= de la caché no es parte del nombre
        destino = os.path.normpath(os.path.join(base, ref))
        if not os.path.exists(destino):
            fallo("%s · referencia a algo que no existe: %s" % (pagina, ref))

for hoja in ("css/estilo.css", "css/fuentes.css"):
    css = leer(hoja)
    base = os.path.dirname(os.path.join(AQUI, hoja))
    for ref in re.findall(r'url\(["\']?([^"\')]+)["\']?\)', css):
        if ref.startswith(("http://", "https://", "data:")):
            continue
        if not os.path.exists(os.path.normpath(os.path.join(base, ref))):
            fallo("%s · url() a algo que no existe: %s" % (hoja, ref))

# ── 2 · Cada ancla tiene su sección ─────────────────────────────────────────

for lang, pagina in PAGINAS:
    html = leer(pagina)
    ids = set(re.findall(r'id="([^"]+)"', html))
    for ancla in re.findall(r'href="#([^"]+)"', html):
        if ancla not in ids:
            fallo("%s · el enlace #%s no lleva a ninguna sección" % (pagina, ancla))

# ── 3 · Las dos lenguas cuentan lo mismo ────────────────────────────────────
#
# No se comparan los textos —son traducciones, no copias— sino la ESTRUCTURA:
# si una página gana una captura o una tarjeta y la otra no, la segunda se ha
# quedado atrás y nadie lo diría hasta abrirla.

conteos = {}
for lang, pagina in PAGINAS:
    html = leer(pagina)
    conteos[lang] = {
        "capturas": len(re.findall(r"<figure[ >]", html)),
        "rasgos":   len(re.findall(r'class="rasgo"', html)),
        "secciones": len(re.findall(r"<section", html)),
        "botones":  len(re.findall(r"data-steam\b", html)),
    }

for clave in conteos["es"]:
    a, b = conteos["es"][clave], conteos["en"][clave]
    if a != b:
        fallo("las dos lenguas no cuadran en «%s»: español %d, inglés %d" % (clave, a, b))

# Y que no estén vacías, que cuadrar en cero también cuadra.
for clave, minimo in (("capturas", 4), ("rasgos", 3), ("botones", 3)):
    if conteos["es"][clave] < minimo:
        fallo("solo hay %d «%s» y hacen falta al menos %d"
              % (conteos["es"][clave], clave, minimo))

# ── 4 · Ninguna novedad se queda sin traducir ───────────────────────────────

js = sin_comentarios(leer(os.path.join("js", "novedades.js")))
n_es = len(re.findall(r"(?<![A-Za-z])es\s*:", js))
n_en = len(re.findall(r"(?<![A-Za-z])en\s*:", js))
if n_es != n_en:
    fallo("novedades.js · %d textos en español y %d en inglés: alguno se ha "
          "quedado sin traducir" % (n_es, n_en))

fechas = re.findall(r'fecha\s*:\s*"([^"]*)"', js)
if not fechas:
    fallo("novedades.js · no hay ni una novedad")
for f in fechas:
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", f):
        fallo("novedades.js · la fecha «%s» no está en AAAA-MM-DD" % f)
if fechas != sorted(fechas, reverse=True):
    fallo("novedades.js · las novedades no van de la más nueva a la más vieja")

# ── 5 · El enlace de Steam vive en un solo sitio ────────────────────────────
#
# El día que exista la ficha se escribe el número en web.js y cambian los dos
# idiomas a la vez. Una URL de tienda escrita a mano dentro de un HTML es la
# que se queda vieja cuando cambia.

for lang, pagina in PAGINAS:
    if "store.steampowered.com" in leer(pagina):
        fallo("%s · hay un enlace de Steam escrito a mano; va en js/web.js" % pagina)

# ── 6 · La vista previa del enlace apunta a algo absoluto ───────────────────
#
# `og:image` en relativo se ve bien en la página y falla justo donde importa:
# buena parte de los clientes de chat y de las redes no resuelven rutas
# relativas, así que el enlace se pega sin imagen y nadie se entera. Y las dos
# páginas tienen que hablar del mismo sitio, o una de las dos manda a la gente
# a un dominio viejo el día que esto se mueva.

dominios = set()
for lang, pagina in PAGINAS:
    html = leer(pagina)
    for etiqueta in ("og:image", "og:url"):
        m = re.search(r'property="%s" content="([^"]+)"' % etiqueta, html)
        if not m:
            fallo("%s · falta la etiqueta %s" % (pagina, etiqueta))
        elif not m.group(1).startswith("http"):
            fallo("%s · %s va en relativo y tiene que ser una URL absoluta: %s"
                  % (pagina, etiqueta, m.group(1)))
        else:
            dominios.add(re.match(r"https?://[^/]+", m.group(1)).group(0))
    m = re.search(r'rel="canonical" href="([^"]+)"', html)
    if m and not m.group(1).startswith("http"):
        fallo("%s · el canonical va en relativo: %s" % (pagina, m.group(1)))

if len(dominios) > 1:
    fallo("las dos páginas apuntan a dominios distintos: %s" % ", ".join(sorted(dominios)))

# ── 7 · Los width/height dicen la verdad, y el CSS deja el alto libre ───────
#
# Los <img> llevan sus medidas escritas para que el navegador reserve el hueco y
# la página no dé saltos al cargar. El precio es que, si esas medidas no son las
# del fichero —o si el CSS fija el ancho y se olvida del alto—, cada imagen sale
# estirada. No da error: solo se ve, y el que mira lo llama «descuadrado».

try:
    from PIL import Image
except ImportError:
    Image = None

css_img = leer("css/estilo.css")
if not re.search(r"^img\s*\{[^}]*height:\s*auto", css_img, re.M):
    fallo("css/estilo.css · las imágenes no llevan `height: auto`, así que el "
          "alto escrito en el HTML se aplica como fijo y las estira")

if Image is not None:
    for lang, pagina in PAGINAS:
        html = leer(pagina)
        base = os.path.dirname(os.path.join(AQUI, pagina))
        for m in re.finditer(r'<img\s+src="([^"]+)"\s+width="(\d+)"\s+height="(\d+)"', html):
            src, w, h = m.group(1), int(m.group(2)), int(m.group(3))
            if src.lower().endswith(".svg"):
                continue
            ruta = os.path.normpath(os.path.join(base, src))
            if not os.path.exists(ruta):
                continue
            im = Image.open(ruta)
            dicho = w / float(h)
            real = im.width / float(im.height)
            if abs(dicho - real) > 0.01:
                fallo("%s · %s dice %d×%d (%.3f) y el fichero es %d×%d (%.3f): "
                      "la imagen saldrá descuadrada"
                      % (pagina, os.path.basename(src), w, h, dicho,
                         im.width, im.height, real))

# ── 8 · La hoja de estilo y el JavaScript llevan su versión al día ──────────
#
# Sin esto, publicar un cambio deja a quien ya haya visitado la web con el CSS
# de antes y el HTML de ahora durante los diez minutos que GitHub Pages cachea
# — y esa mezcla rompe cosas que ninguna de las dos versiones rompía por su
# cuenta. `versionar.py` pone un resumen del contenido en la URL; esto se
# limita a comprobar que no se ha olvidado.

import hashlib

for rel in ("css/fuentes.css", "css/estilo.css", "js/novedades.js", "js/web.js"):
    with io.open(os.path.join(AQUI, rel), "rb") as f:
        v = hashlib.sha256(f.read()).hexdigest()[:6]
    for lang, pagina in PAGINAS:
        html = leer(pagina)
        m = re.search(re.escape(rel) + r"\?v=([0-9a-f]+)", html)
        if not m:
            fallo("%s · %s se enlaza sin versión: al publicar, un navegador con "
                  "caché mezclará ficheros viejos y nuevos" % (pagina, rel))
        elif m.group(1) != v:
            fallo("%s · %s enlaza la versión %s y el fichero es %s: falta pasar "
                  "versionar.py" % (pagina, rel, m.group(1), v))

# ── Resultado ───────────────────────────────────────────────────────────────

print("Web · %d páginas · %d capturas · %d novedades"
      % (len(PAGINAS), conteos["es"]["capturas"], len(fechas)))

if fallos:
    print("\n%d fallo(s):" % len(fallos))
    for f in fallos:
        print("  ✗ " + f)
    sys.exit(1)

print("Todo en su sitio.")
