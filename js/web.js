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
