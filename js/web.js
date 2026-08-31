/* ───────────────────────────────────────────────────────────────────────────
   Lo poco que la web hace con JavaScript: pintar las novedades y resolver el
   enlace a Steam. Todo lo demás es HTML y CSS, para que la página siga siendo
   legible con el JavaScript apagado.

   **El enlace a Steam vive en UN sitio.** Mientras `STEAM_APPID` esté vacío,
   los botones se pintan apagados y dicen que la ficha aún no está publicada.
   El día que exista, se escribe el número aquí y cambian los dos idiomas y
   todos los botones a la vez: un enlace re-tecleado en cuatro sitios es un
   enlace que el día que cambia se queda a medias en tres.
   ─────────────────────────────────────────────────────────────────────────── */

const STEAM_APPID = "";      // ← el número de la ficha, cuando la haya

const STEAM_URL = STEAM_APPID
  ? "https://store.steampowered.com/app/" + STEAM_APPID + "/"
  : "";

const TEXTOS = {
  es: {
    wishlist:  "Añadir a la lista de deseados",
    pronto:    "Pronto en Steam",
    aviso:     "La ficha de Steam todavía no está publicada.",
    sinjs:     "Las novedades necesitan JavaScript. Sin él, el resto de la página se lee igual.",
    locale:    "es-ES"
  },
  en: {
    wishlist:  "Add to your wishlist",
    pronto:    "Coming to Steam",
    aviso:     "The Steam page isn't live yet.",
    sinjs:     "The news list needs JavaScript. Without it, the rest of the page reads the same.",
    locale:    "en-GB"
  }
};

(function () {
  "use strict";

  const lang = (document.documentElement.lang || "es").slice(0, 2);
  const t = TEXTOS[lang] || TEXTOS.es;

  /* ── Los botones de Steam ────────────────────────────────────────────── */

  document.querySelectorAll("[data-steam]").forEach(function (a) {
    const etiqueta = a.querySelector("[data-steam-texto]") || a;
    if (STEAM_URL) {
      a.href = STEAM_URL;
      a.removeAttribute("aria-disabled");
      etiqueta.textContent = t.wishlist;
    } else {
      a.removeAttribute("href");
      a.setAttribute("aria-disabled", "true");
      etiqueta.textContent = t.pronto;
    }
  });

  document.querySelectorAll("[data-steam-aviso]").forEach(function (n) {
    n.textContent = STEAM_URL ? "" : t.aviso;
  });

  /* ── Las novedades ───────────────────────────────────────────────────── */

  const caja = document.querySelector("[data-novedades]");

  if (caja && typeof NOVEDADES !== "undefined") {
    const tope = parseInt(caja.getAttribute("data-novedades"), 10) || NOVEDADES.length;

    caja.innerHTML = NOVEDADES.slice(0, tope).map(function (n) {
      // La fecha se guarda en ISO y se escribe en el formato de cada idioma:
      // el 31/08 de un lector español es el August 31 de uno inglés, y eso no
      // es una traducción que haya que escribir a mano en el fichero de datos.
      const d = new Date(n.fecha + "T12:00:00");
      const legible = d.toLocaleDateString(t.locale, {
        year: "numeric", month: "long", day: "numeric"
      });

      return '<article class="novedad">' +
               '<div class="novedad-meta">' +
                 '<time datetime="' + n.fecha + '">' + legible + '</time>' +
                 '<span class="etiqueta">' + texto(n.etiqueta) + '</span>' +
               '</div>' +
               '<div>' +
                 '<h3>' + texto(n.titulo) + '</h3>' +
                 '<p>' + texto(n.cuerpo) + '</p>' +
               '</div>' +
             '</article>';
    }).join("");
  }

  document.querySelectorAll("[data-sinjs]").forEach(function (n) {
    n.textContent = t.sinjs;
  });

  /* ── Aparecer al llegar, y el fondo del hero un poco más lento ───────── */
  /*
     La guía de diseño pide movimiento con sentido y prohíbe una sola duración
     para todo. Aquí el movimiento dice exactamente una cosa —«esto acaba de
     entrar en pantalla»— y el fondo que se mueve más despacio que el texto es
     lo único que queda de «profundidad» sin meter un motor 3D en una landing.

     Las dos cosas se apagan si el sistema pide menos movimiento, y las dos
     degradan a nada si no hay JavaScript: el estado por defecto del CSS es
     visible, así que una página sin JS se lee entera igual.
  */

  const quieto = window.matchMedia
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const revelables = document.querySelectorAll(".revela");

  if (quieto || !("IntersectionObserver" in window)) {
    revelables.forEach(function (n) { n.classList.add("dentro"); });
  } else {
    const vigia = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("dentro");
          vigia.unobserve(e.target);   // una vez visto, deja de vigilarse
        }
      });
    }, { rootMargin: "0px 0px -12% 0px", threshold: 0.08 });
    revelables.forEach(function (n) { vigia.observe(n); });

    const fondo = document.querySelector("[data-parallax]");
    if (fondo) {
      let pedido = false;
      window.addEventListener("scroll", function () {
        if (pedido) return;
        pedido = true;
        // El trabajo va dentro de requestAnimationFrame: mover una capa en cada
        // evento de scroll es cómo se consigue que una página vaya a tirones.
        window.requestAnimationFrame(function () {
          const y = window.scrollY;
          if (y < window.innerHeight) {
            fondo.style.transform = "translate3d(0," + (y * 0.18) + "px,0)";
          }
          pedido = false;
        });
      }, { passive: true });
    }
  }

  /* ── El hero encadena varias tomas ───────────────────────────────────── */
  /*
     Una captura fija se lee como un cartel; tres encadenadas con un fundido
     lento se leen como un juego. Van del mismo sitio y a distintos ángulos a
     propósito: saltar de barrio en barrio marea, girar alrededor de uno no.
  */

  const capas = document.querySelectorAll(".hero-capa");
  if (capas.length > 1 && !quieto) {
    let i = 0;
    setInterval(function () {
      capas[i].classList.remove("viva");
      i = (i + 1) % capas.length;
      capas[i].classList.add("viva");
    }, 6000);
  }

  /* ── La carta se inclina con el ratón ────────────────────────────────── */
  /*
     Es lo único de esta página con lo que se puede jugar, y en una web de un
     juego de cartas eso no es un adorno: es la muestra del producto. El brillo
     del foil se mueve con la inclinación, que es lo que separa una lámina de
     un rectángulo pintado.
  */

  const escena = document.querySelector(".carta-escena");
  const carta = document.querySelector(".carta");

  if (escena && carta && !quieto) {
    const TOPE = 13;   // grados: más que esto y deja de parecer una carta

    function inclinar(px, py) {
      const c = escena.getBoundingClientRect();
      const x = (px - c.left) / c.width  - 0.5;
      const y = (py - c.top)  / c.height - 0.5;
      carta.style.setProperty("--ry", ( x * TOPE * 2).toFixed(2) + "deg");
      carta.style.setProperty("--rx", (-y * TOPE * 2).toFixed(2) + "deg");
      carta.style.setProperty("--foil", (115 + x * 90).toFixed(0) + "deg");
    }

    escena.addEventListener("mousemove", function (e) { inclinar(e.clientX, e.clientY); });
    escena.addEventListener("touchmove", function (e) {
      if (e.touches[0]) inclinar(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: true });

    function soltar() {
      carta.style.setProperty("--rx", "0deg");
      carta.style.setProperty("--ry", "0deg");
      carta.style.setProperty("--foil", "115deg");
    }
    escena.addEventListener("mouseleave", soltar);
    escena.addEventListener("touchend", soltar);
  }

  /* ── La barra se cierra al bajar ─────────────────────────────────────── */
  /*
     Sobre el hero va transparente y deja ver la ciudad; en cuanto la página se
     mueve, se cierra con su fondo y su filo. Una barra opaca desde el primer
     píxel recorta justo la imagen que la portada viene a enseñar.
  */

  const barra = document.querySelector(".barra");
  if (barra) {
    function mirar() { barra.classList.toggle("pegada", window.scrollY > 40); }
    window.addEventListener("scroll", mirar, { passive: true });
    mirar();
  }

  /* ── Las cifras cuentan al llegar ────────────────────────────────────── */
  /*
     Contar hasta el número dice «esto es una cantidad» mejor que el número
     quieto, y dura lo justo para verse una vez. Con `prefers-reduced-motion`
     no se anima: el valor final ya está escrito en el HTML, así que sin JS y
     sin animación la cifra se lee igual.
  */

  const cifras = document.querySelectorAll("[data-cuenta]");
  if (cifras.length && !quieto && "IntersectionObserver" in window) {
    const ojo = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) {
        if (!e.isIntersecting) return;
        ojo.unobserve(e.target);
        const fin = parseInt(e.target.getAttribute("data-cuenta"), 10);
        const dura = 900;
        const t0 = performance.now();
        (function paso(t) {
          const k = Math.min(1, (t - t0) / dura);
          // frenada al final: llega al número y se para, no lo alcanza de golpe
          const suave = 1 - Math.pow(1 - k, 3);
          e.target.textContent = String(Math.round(fin * suave));
          if (k < 1) requestAnimationFrame(paso);
        })(t0);
      });
    }, { threshold: 0.5 });
    cifras.forEach(function (n) { ojo.observe(n); });
  }

  /* ── El año del pie ──────────────────────────────────────────────────── */

  document.querySelectorAll("[data-anyo]").forEach(function (n) {
    n.textContent = String(new Date().getFullYear());
  });

  /* Un texto que falte en un idioma cae al español, que es donde se escribe
     primero — igual que hace el juego, que cae al inglés y luego a la propia
     clave antes que dejar un hueco. Un hueco se lee como una página rota. */
  function texto(campo) {
    if (!campo) return "";
    return campo[lang] || campo.es || campo.en || "";
  }
})();
