# La web de Ryujindo Card Shop

Una página estática, en español e inglés, para llevar gente a la lista de
deseados de Steam y contar en qué anda el desarrollo. **Sin dependencias, sin
compilación y sin marco de trabajo**: son HTML, CSS y sesenta líneas de
JavaScript, así que se abre con doble clic y se publica copiando la carpeta.

```
  index.html          español
  en/index.html       inglés
  css/estilo.css      la maqueta, común a las dos lenguas
  css/fuentes.css     las dos familias, servidas desde fonts/ y no desde Google
  design-system/      el sistema del que sale la maqueta — leerlo antes de tocar
  fonts/              los .woff2 latinos + el texto de la OFL que exige llevarlos
  js/novedades.js     ← LAS NOVEDADES, en un solo sitio y en los dos idiomas
  js/web.js           pinta las novedades y resuelve el enlace a Steam
  img/                lo genera imagenes.py — no se edita a mano
  imagenes.py         prepara capturas y marca desde el juego y desde arte/marca
  comprobar.py        dice si algo está roto antes de subirlo
  servir.py           la sirve en local para verla como se verá
  arte/marca/         los SVG de los que salen el logotipo y el favicon
```

---

## Las tres cosas que se hacen aquí

### 1 · Escribir una novedad

Se añade un objeto **arriba** del array de [`js/novedades.js`](js/novedades.js),
con su texto en español y en inglés. No hay un segundo sitio que tocar: las dos
páginas leen de ahí, y la fecha se escribe en el formato de cada idioma sola.

```js
{
  fecha: "2026-09-04",
  etiqueta: { es: "Mundo", en: "World" },
  titulo:   { es: "…", en: "…" },
  cuerpo:   { es: "…", en: "…" }
}
```

### 2 · Rehacer las imágenes

```bash
python3 imagenes.py
```

Coge las capturas de `/private/tmp/kitsune/shots` —las que deja el `./jugar.sh
-shots` del repositorio del juego, que vive aparte— y la marca de
`arte/marca/*.svg`, y escribe `web/img/` entero: cada
captura en dos tamaños **y en WebP** —medido, un 48 % menos que el JPEG a la
misma calidad—, los tres logotipos, el favicon y la imagen que se ve cuando
alguien pega el enlace en un chat, que sí va en JPEG porque hay scrapers que no
leen WebP.

**Qué capturas salen y en qué orden lo decide la tabla `CAPTURAS`** de ese
fichero; los pies de foto están en el HTML de cada idioma. Cambiar la galería es
cambiar la tabla, mover los `<figure>` y volver a lanzarlo.

Se niega a trabajar si hay una pasada del juego viva: `-shots` **vacía** la
carpeta al empezar, así que a mitad de pasada la mitad de las capturas son de
ayer y la otra mitad no existen todavía.

### 3 · Mirarla y comprobarla

```bash
python3 servir.py        # http://localhost:8765
python3 comprobar.py     # devuelve 1 si algo está roto
```

El comprobador mira seis cosas, y las seis están escritas porque ninguna la
canta el navegador: que todo lo que se referencia desde el HTML exista, que
**las `url()` del CSS también** —ahí viven las fuentes y la imagen del hero, y
si falta una la página cae al respaldo y parece que nadie la cambió—, que cada
ancla lleve a una sección, que **las dos lenguas cuenten lo mismo** (misma
cantidad de capturas, de tarjetas y de llamadas a la acción), que ninguna
novedad se haya quedado sin traducir, y que nadie haya escrito el enlace de
Steam a mano dentro de un HTML.

Ese guardián de `url()` se estrenó cazando un fallo de verdad a los dos minutos
de existir: al pasar las capturas a WebP, el CSS seguía pidiendo
`img/cruce.jpg` y **el hero se había quedado sin fondo**.

---

## El enlace a Steam

Está en **un** sitio: `STEAM_APPID`, arriba de [`js/web.js`](js/web.js). Mientras
esté vacío, los botones salen apagados y dicen que la ficha no está publicada.
El día que exista la ficha se escribe el número ahí y cambian los dos idiomas y
los cuatro botones a la vez.

---

## Publicarla

Este repositorio **es** el sitio: GitHub Pages lo sirve tal cual desde la raíz de
`main`. Rutas relativas, sin nada que compilar y sin acción de despliegue — se
hace `git push` y en un minuto está publicado.

Vive aparte del repositorio del juego a propósito, y no por orden: aquél lleva
los packs de assets comprados, cuya licencia permite meterlos en el juego y
**prohíbe distribuirlos de forma extraíble**. Un repositorio público con ellos
dentro sería exactamente eso. Aquí solo hay web: HTML, CSS, las capturas ya
exportadas y la marca.

Antes de subirla por primera vez quedan tres cosas, apuntadas en `PENDIENTE.md`:

- **Las `og:` apuntan a rutas relativas.** Muchos chats y redes exigen una URL
  absoluta para la imagen de vista previa, así que el día que haya dominio hay
  que escribirlo en las cuatro etiquetas `og:image` y en `canonical`.
- **Las capturas llevan el HUD del juego**, minimapa incluido. Para una web se
  quieren limpias, y eso se arregla en el juego —un modo de captura sin
  interfaz— y no recortando PNG.
- **Regenerar las imágenes necesita el juego.** Las capturas salen de una pasada
  de `-shots`, que vive en el otro repositorio. Publicar no lo necesita —las
  imágenes ya exportadas están aquí commiteadas—; rehacerlas sí.

---

## Por qué está hecha así

Las decisiones que parecen raras y no lo son:

- **Los textos fijos están escritos dos veces, uno por idioma, y las novedades
  no.** El pitch cambia dos veces al año y una traducción a medias se ve al
  abrir la página; las novedades cambian cada semana y ahí sí duele tener dos
  ficheros. La duplicación se paga donde es barata.
- **La marca va en SVG.** Es lo primero que ve quien llega, y un mapa de bits al
  doble de tamaño se ve blando en una pantalla densa. Lo que no puede ser
  vectorial —el favicon, la imagen de enlace— se rasteriza del mismo SVG con el
  navegador que ya hay en la máquina, para que no exista una segunda copia de la
  marca que se quede vieja.
- **El velo del hero cae en curva suave.** El juego se dejó el título de su
  propio menú a un 0,006 de opacidad cuatro veces seguidas por usar una caída
  cuadrática (trampas 206, 280, 335 y 377). La misma cuenta, el mismo error.
- **La maqueta sale de `design-system/ryujindo-card-shop/MASTER.md`**, generado
  con la guía de diseño instalada: patrón *Feature-Rich Showcase*, superficie
  oscura, verde tapete y oro, profundidad por capas y 200-300 ms de transición.
  Dos cosas se apartan de él a propósito, y las dos están razonadas en la
  cabecera de `estilo.css`: la tipografía —proponía una manuscrita artesanal
  para «indie», y la ficha de sitios japoneses da Noto Serif JP + Noto Sans JP,
  que además es la letra que el juego lleva dentro— y el rojo, que lo manda el
  logotipo y no una paleta.
- **Los titulares van en mincho.** Es la letra de los rótulos y los libros
  japoneses, y comparte con el logotipo la lógica del trazo modulado que una
  grotesca no tiene. Solo en titulares: en cuerpo pequeño una serif japonesa
  pierde. Y las fuentes viajan dentro de la web, no enlazadas a Google.
- **La llamada a Steam está en tres sitios** —barra, portada y final— porque es
  lo que pide el patrón de landing para este tipo de producto, y la de la barra
  es la única que está siempre a la vista.
- **Hay un comprobador.** Una web de dos idiomas se rompe por sitios que no dan
  error, y el más caro es que una lengua se quede atrás sin que nadie lo note.
