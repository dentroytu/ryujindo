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
        "capturas": len(re.findall(r"<figure>", html)),
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

# ── Resultado ───────────────────────────────────────────────────────────────

print("Web · %d páginas · %d capturas · %d novedades"
      % (len(PAGINAS), conteos["es"]["capturas"], len(fechas)))

if fallos:
    print("\n%d fallo(s):" % len(fallos))
    for f in fallos:
        print("  ✗ " + f)
    sys.exit(1)

print("Todo en su sitio.")
