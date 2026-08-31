#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prepara las imágenes de la web a partir de las que genera el juego.

**Para qué.** La web enseña capturas del juego y la marca. Las capturas las
produce el propio juego con un comando (`-shots`) y la marca sale de una hoja de
arte con las tres versiones juntas, que se recorta aquí. Una imagen recortada a
mano se queda vieja el día que cambia lo que retrata y no lo dice — el proyecto
ya pagó esa factura con las dos previas de carta que seguían enseñando un campo
que ya no existía (trampa 88). Aquí la lista de lo que sale en la web es **esta
tabla**, y rehacerla es un comando.

**Cómo se usa:**

    python3 web/imagenes.py                      # con las capturas de /private/tmp/kitsune
    python3 web/imagenes.py --shots /otra/carpeta --capsulas /otra/capsulas

Cada captura sale en dos tamaños: la grande (1600 px) para el hero y para verla
a pantalla completa, y la de rejilla (800 px). De la hoja de marca salen las tres
piezas —el logotipo horizontal, el apilado y el emblema— separadas por
componentes conexos y recortadas a su tinta, sin coordenadas escritas a mano: una
caja a mano se queda vieja en cuanto la hoja se rehaga con las piezas movidas.
Y de la primera captura más el logotipo se compone la imagen que se ve cuando
alguien pega el enlace en un chat, que es la única imagen de la web que nadie
mira nunca hasta que sale mal.

Falla —y dice cuál falta— si un origen no está. Un hueco silencioso en la web
se lee como un fallo de la web, no como una captura que nadie generó.
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    from PIL import Image
except ImportError:
    sys.exit("hace falta Pillow:  python3 -m pip install --user Pillow")

AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(AQUI, "img")

ANCHO_GRANDE = 2000
ANCHO_REJILLA = 1100
CALIDAD = 80

# (fichero de -shots, nombre en la web)
#
# El orden es el de la galería. Cambiar la galería es cambiar esta tabla y
# volver a lanzar el guion; los pies de foto viven en el HTML de cada idioma.
CAPTURAS = [
    # El hero encadena tres tomas, y de tres sitios distintos: hasta que las
    # capturas no salieron sin HUD, las únicas limpias eran del cruce y las tres
    # eran el mismo sitio.
    ("56-cruce.png",            "cruce"),
    ("50-akihabara-skyline.png","cruce2"),
    ("64-nakano-shotengai.png", "cruce3"),

    # Los tres pasos
    ("29-kenji-oferta.png",     "kenji"),
    ("36-carpeta.png",          "carpeta"),
    ("43b-local.png",           "local"),

    # La galería, en el orden en que sale
    ("01-fachada.png",          "tienda"),
    ("25-apertura.png",         "apertura"),
    ("67-ficha.png",            "ficha"),
    ("68-duelo.png",            "duelo"),
    ("54-yokocho-dentro.png",   "yokocho"),
    ("63-parque-hokora.png",    "parque"),
    ("49-akihabara.png",        "akihabara"),
    ("76-ramen-dentro.png",     "ramen"),
    ("05-mesas.png",            "mesas"),
    ("72-konbini-dentro.png",   "konbini"),
]

# La marca. Son **cinco ficheros**, uno por pieza, en `arte/marca/`: no hay nada
# que recortar ni que adivinar. Antes venían todas en una hoja y había que
# separarlas por grupos de píxeles que se tocan; con el kit hecho, eso sobra —
# y lo que sobra no puede fallar.
MARCA_DIR = os.path.join(AQUI, "arte", "marca")

MARCA = [
    # (fichero, nombre en la web, ancho)
    ("logotipo-horizontal.png", "logotipo.webp", 1800),   # el hero
    ("emblema.png",             "emblema.webp",   512),   # la barra y el favicon
    ("logotipo-apilado.png",    "apilado.webp",   900),   # cajas altas y móvil
    ("tienda.png",              "tienda-marca.webp", 900),
]

FAVICON = 180

# La imagen que se ve al pegar el enlace en un chat o en una red. Se compone del
# fondo del hero y del logotipo, así que cambia sola el día que cambie cualquiera
# de los dos.
OG_ANCHO, OG_ALTO = 1200, 630


def escalar(origen, destino, ancho, calidad=CALIDAD):
    """
    Las capturas salen en WebP: medido sobre estas nueve, pesa un 48 % menos que
    el JPEG a calidad equivalente, y a una landing la carga de imágenes es lo
    único que la hace lenta. La de enlace compartido se queda en JPEG aparte,
    porque hay scrapers de chat que no leen WebP y ésa se ve fuera de la web.
    """
    im = Image.open(origen).convert("RGB")
    if im.width > ancho:
        alto = round(im.height * ancho / im.width)
        im = im.resize((ancho, alto), Image.LANCZOS)
    im.save(destino, "WEBP", quality=calidad - 2, method=6)
    return os.path.getsize(destino), im.size


def imagen_de_enlace(captura, logotipo, salida):
    """
    La imagen que se ve al pegar el enlace: la captura del hero, oscurecida, con
    el logotipo encima. 1200 × 630 es lo que piden las redes y los chats.
    """
    fondo = Image.open(captura).convert("RGB")
    # Recorte central a la proporción pedida, para no deformar la captura.
    prop = OG_ANCHO / float(OG_ALTO)
    if fondo.width / float(fondo.height) > prop:
        ancho = int(fondo.height * prop)
        caja = ((fondo.width - ancho) // 2, 0, (fondo.width + ancho) // 2, fondo.height)
    else:
        alto = int(fondo.width / prop)
        caja = (0, (fondo.height - alto) // 2, fondo.width, (fondo.height + alto) // 2)
    fondo = fondo.crop(caja).resize((OG_ANCHO, OG_ALTO), Image.LANCZOS)

    # El velo: sin él, un logotipo claro sobre un cielo claro no se lee. Es la
    # misma cuenta que el velo del hero, y por la misma razón.
    velo = Image.new("RGBA", (OG_ANCHO, OG_ALTO), (20, 21, 28, 0))
    tinta = velo.load()
    for y in range(OG_ALTO):
        t = y / float(OG_ALTO - 1)
        a = int(255 * (0.30 + 0.55 * (t ** 0.6)))
        for x in range(OG_ANCHO):
            tinta[x, y] = (20, 21, 28, a)
    fondo = Image.alpha_composite(fondo.convert("RGBA"), velo)

    marca = logotipo
    fondo.alpha_composite(marca, ((OG_ANCHO - marca.width) // 2,
                                  (OG_ALTO - marca.height) // 2))

    fondo.convert("RGB").save(salida, "JPEG", quality=88, optimize=True)
    return os.path.getsize(salida), (OG_ANCHO, OG_ALTO)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--shots", default="/private/tmp/kitsune/shots-limpio")
    p.add_argument("--capsulas", default="/private/tmp/kitsune/capsulas")
    p.add_argument("--emblema", default="/private/tmp/kitsune")
    p.add_argument("--marca", default=MARCA_DIR,
                   help="carpeta con los SVG de la marca")
    args = p.parse_args()

    fuentes = {"shots": args.shots, "capsulas": args.capsulas, "emblema": args.emblema}

    # Con una pasada de capturas viva, la carpeta está a medio llenar: `-shots`
    # la vacía al empezar y la va rellenando. Coger las imágenes de ahí en ese
    # momento da una web con la mitad de las capturas de ayer y la mitad de hoy,
    # o directamente un fichero que no está. Es la trampa 94 del proyecto, y se
    # paga igual aquí. (`ps -o comm=` da solo el ejecutable: con la línea entera,
    # el propio grep y su shell se cuentan a sí mismos — trampa 132.)
    try:
        vivos = subprocess.run(["ps", "-A", "-o", "comm="], capture_output=True,
                               text=True).stdout
        if "Ryujindo Card Shop" in vivos:
            sys.exit("hay una pasada del juego corriendo: la carpeta de capturas "
                     "se está reescribiendo ahora mismo. Espera a que acabe.")
    except OSError:
        pass

    faltan = [f for f, _ in CAPTURAS if not os.path.exists(os.path.join(args.shots, f))]
    marca_dir = args.marca
    faltan += [os.path.join(marca_dir, f) for f, _, _ in MARCA
               if not os.path.exists(os.path.join(marca_dir, f))]
    if faltan:
        sys.exit("faltan estos originales, hay que generarlos con el juego:\n  "
                 + "\n  ".join(faltan))

    os.makedirs(DESTINO, exist_ok=True)
    total = 0

    for fichero, nombre in CAPTURAS:
        origen = os.path.join(args.shots, fichero)
        for sufijo, ancho in (("", ANCHO_GRANDE), ("-r", ANCHO_REJILLA)):
            salida = os.path.join(DESTINO, nombre + sufijo + ".webp")
            peso, tam = escalar(origen, salida, ancho)
            total += peso
            print("  %-22s %4d×%-4d %6.0f KB" % (os.path.basename(salida),
                                                 tam[0], tam[1], peso / 1024))

    piezas = {}
    for fuente, nombre, ancho in MARCA:
        im = Image.open(os.path.join(marca_dir, fuente)).convert("RGBA")
        bb = im.split()[3].getbbox()          # a su tinta, sin aire alrededor
        if bb:
            im = im.crop(bb)
        if im.width > ancho:
            im = im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS)
        salida = os.path.join(DESTINO, nombre)
        im.save(salida, "WEBP", quality=90, method=6)
        piezas[nombre] = im
        peso = os.path.getsize(salida)
        total += peso
        print("  %-22s %4d×%-4d %6.0f KB" % (nombre, im.width, im.height, peso / 1024))

    # El favicon sale del emblema —el cuadrado con la máscara, que es la única
    # pieza que se sigue leyendo a 32 px— y va en PNG, que es lo que entienden
    # todos los navegadores y los atajos de escritorio.
    emb = piezas["emblema.webp"]
    fav = emb.resize((FAVICON, round(emb.height * FAVICON / emb.width)), Image.LANCZOS)
    salida = os.path.join(DESTINO, "favicon.png")
    fav.save(salida, "PNG", optimize=True)
    peso = os.path.getsize(salida)
    total += peso
    print("  %-22s %4d px      %6.0f KB" % ("favicon.png", FAVICON, peso / 1024))

    salida = os.path.join(DESTINO, "og.jpg")
    logo = piezas["logotipo.webp"]
    ancho_og = int(OG_ANCHO * 0.78)
    logo_og = logo.resize((ancho_og, round(logo.height * ancho_og / logo.width)),
                          Image.LANCZOS)
    peso, tam = imagen_de_enlace(os.path.join(args.shots, CAPTURAS[0][0]), logo_og, salida)
    total += peso
    print("  %-22s %4d×%-4d %6.0f KB" % ("og.jpg", tam[0], tam[1], peso / 1024))

    print("\n%d imágenes · %.1f MB en total" % (len(CAPTURAS) * 2 + len(MARCA) + 2,
                                                total / 1024 / 1024))


if __name__ == "__main__":
    main()
