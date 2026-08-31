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

ANCHO_GRANDE = 1600
ANCHO_REJILLA = 800
CALIDAD = 82

# (fichero de -shots, nombre en la web)
#
# El orden es el de la galería. Cambiar la galería es cambiar esta tabla y
# volver a lanzar el guion; los pies de foto viven en el HTML de cada idioma.
CAPTURAS = [
    ("56-cruce.png",          "cruce"),        # el hero
    ("29-kenji-oferta.png",   "kenji"),        # el paso 1: el problema
    ("43b-local.png",         "local"),        # el paso 3: la meta
    ("25-apertura.png",       "apertura"),
    ("67-ficha.png",          "ficha"),
    ("68-duelo.png",          "duelo"),
    ("54-yokocho-dentro.png", "yokocho"),
    ("63-parque-hokora.png",  "parque"),
    ("50-akihabara-skyline.png", "akihabara"),
    ("36-carpeta.png",        "carpeta"),
    ("75-ramen.png",          "ramen"),
]

# La marca. El origen son los SVG de `arte/marca/`, que es lo que se dibujó:
# vectorial se ve nítido a cualquier tamaño y en cualquier pantalla, y en la web
# va tal cual. Lo que NO puede ser vectorial —el favicon y la imagen de enlace,
# que las consumen navegadores y chats como mapa de bits— se rasteriza aquí del
# mismo SVG. Un PNG dibujado aparte sería una segunda copia de la marca, y una
# segunda copia es la que se queda vieja (trampa 112).
MARCA_DIR = os.path.join(AQUI, "arte", "marca")

MARCA = [
    ("ryujindo_horizontal.svg", "logotipo.svg"),   # el hero
    ("ryujindo_vertical.svg",   "apilado.svg"),    # de repuesto, para cajas altas
    ("ryujindo_emblem.svg",     "emblema.svg"),    # la barra
]

# Rasterizados del SVG, para donde no vale un vector.
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


def rasterizar(svg, ancho, salida):
    """
    Convierte un SVG en PNG con fondo transparente, al ancho pedido.

    Lo hace el navegador que ya está en la máquina: Pillow no lee SVG, y meter
    un rasterizador propio para dos ficheros sería más código del que hay web.
    Si no hay navegador, se dice — y se dice qué falta, no «error».
    """
    chrome = None
    for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"):
        if os.path.exists(c):
            chrome = c
            break
    if chrome is None:
        sys.exit("para rasterizar la marca hace falta Chrome, Chromium o Edge "
                 "instalado. Todo lo demás de la web se genera sin él.")

    # El SVG dice su tamaño en la cabecera; de ahí sale el alto que toca.
    cabecera = io.open(svg, encoding="utf-8").read(400)
    w = float(re.search(r'width="([\d.]+)"', cabecera).group(1))
    h = float(re.search(r'height="([\d.]+)"', cabecera).group(1))
    alto = int(round(ancho * h / w))

    tmp = tempfile.mkdtemp()
    envoltorio = os.path.join(tmp, "marca.html")
    io.open(envoltorio, "w", encoding="utf-8").write(
        '<!doctype html><meta charset="utf-8">'
        '<style>html,body{margin:0;padding:0;background:transparent}'
        'img{display:block;width:%dpx;height:%dpx}</style>'
        '<img src="%s">' % (ancho, alto, "file://" + os.path.abspath(svg)))

    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1",
                    "--default-background-color=00000000",
                    "--window-size=%d,%d" % (ancho, alto),
                    "--virtual-time-budget=4000",
                    "--screenshot=" + os.path.abspath(salida),
                    "--allow-file-access-from-files",
                    "file://" + envoltorio],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(tmp, ignore_errors=True)

    if not os.path.exists(salida):
        sys.exit("el navegador no llegó a escribir %s" % salida)
    return Image.open(salida).convert("RGBA")


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
    p.add_argument("--shots", default="/private/tmp/kitsune/shots")
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
    faltan += [os.path.join(marca_dir, f) for f, _ in MARCA
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

    for fuente, nombre in MARCA:
        salida = os.path.join(DESTINO, nombre)
        shutil.copyfile(os.path.join(marca_dir, fuente), salida)
        peso = os.path.getsize(salida)
        total += peso
        print("  %-22s vectorial    %6.0f KB" % (nombre, peso / 1024))

    salida = os.path.join(DESTINO, "favicon.png")
    rasterizar(os.path.join(marca_dir, "ryujindo_emblem.svg"), FAVICON, salida)
    peso = os.path.getsize(salida)
    total += peso
    print("  %-22s %4d px      %6.0f KB" % ("favicon.png", FAVICON, peso / 1024))

    logo = rasterizar(os.path.join(marca_dir, "ryujindo_horizontal.svg"),
                      int(OG_ANCHO * 0.66),
                      os.path.join(DESTINO, ".logo-og.png"))
    salida = os.path.join(DESTINO, "og.jpg")
    peso, tam = imagen_de_enlace(os.path.join(args.shots, CAPTURAS[0][0]), logo, salida)
    os.remove(os.path.join(DESTINO, ".logo-og.png"))
    total += peso
    print("  %-22s %4d×%-4d %6.0f KB" % ("og.jpg", tam[0], tam[1], peso / 1024))

    print("\n%d imágenes · %.1f MB en total" % (len(CAPTURAS) * 2 + len(MARCA) + 2,
                                                total / 1024 / 1024))


if __name__ == "__main__":
    main()
