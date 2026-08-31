#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera `en/index.html` a partir de `index.html`.

**Para qué.** Las dos páginas son la misma maqueta con distinto texto. Editadas
a mano, la inglesa se queda atrás en cuanto la española crece — y no da ningún
error: sale una página en inglés a la que le falta una sección, y solo se ve
abriéndola. Aquí la estructura se copia sola y lo único que se mantiene a mano
es **el diccionario de abajo**, que es lo que de verdad hay que traducir.

**Cómo se usa:**

    python3 traducir.py           # reescribe en/index.html
    python3 traducir.py --seco    # dice qué haría y qué no sabe traducir

Avisa —y devuelve 1— si al terminar queda texto que parece español, que es la
señal de que hay una frase nueva sin su pareja en el diccionario.
"""
import io
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

# Lo que cambia entre las dos páginas y no es texto: rutas y etiquetas de idioma.
ESTRUCTURA = [
    ('lang="es"', 'lang="en"'),
    ('href="img/', 'href="../img/'),
    ('src="img/', 'src="../img/'),
    ("url('img/", "url('../img/"),
    ('href="css/', 'href="../css/'),
    ('src="js/', 'src="../js/'),
    ('<a href="index.html" aria-current="true" hreflang="es">ES</a>',
     '<a href="../index.html" hreflang="es">ES</a>'),
    ('<a href="en/index.html" hreflang="en">EN</a>',
     '<a href="index.html" aria-current="true" hreflang="en">EN</a>'),
    ('<link rel="canonical" href="https://dentroytu.github.io/ryujindo/">',
     '<link rel="canonical" href="https://dentroytu.github.io/ryujindo/en/">'),
    ('<meta property="og:url" content="https://dentroytu.github.io/ryujindo/">',
     '<meta property="og:url" content="https://dentroytu.github.io/ryujindo/en/">'),
    ('<meta property="og:locale" content="es_ES">',
     '<meta property="og:locale" content="en_GB">'),
    ('id="como-se-juega"', 'id="how-it-plays"'),
    ('href="#como-se-juega"', 'href="#how-it-plays"'),
    ('id="capturas"', 'id="screenshots"'),
    ('href="#capturas"', 'href="#screenshots"'),
    ('id="novedades"', 'id="news"'),
    ('href="#novedades"', 'href="#news"'),
    ('id="la-carta"', 'id="the-card"'),
    ('id="cifras"', 'id="numbers"'),
]

# El diccionario. Clave: el texto tal cual aparece en la página española.
# Se traduce la frase entera y no palabra a palabra: en el diálogo y en el tono
# manda el guion del juego, no el buen inglés — el jugador habla en corto y
# Kenji nunca se disculpa.
TEXTOS = {
"Ryujindo Card Shop — simulador de tienda de cartas en Japón":
    "Ryujindo Card Shop — a card shop sim set in Japan",
"Heredas las cajas de tu abuela y un cuarto de seis tatamis. Aprende a tasar, elige por dónde vendes y llega a alquilar el local de la esquina. Simulador de tienda de cartas TCG ambientado en Japón.":
    "You inherit your grandmother's boxes and a six-tatami room. Learn to appraise, choose where you sell, and work your way to the empty shop around the corner. A TCG card shop simulator set in Japan.",
"Te compró la carta de tu abuela por una décima parte de lo que valía. Aprende lo suficiente para que no vuelva a pasar.":
    "He bought your grandmother's card for a tenth of what it was worth. Learn enough that it doesn't happen again.",
"Cómo se juega": "How it plays",
"Capturas": "Screenshots",
"Novedades": "News",
"Pronto en Steam": "Coming to Steam",
"Sigue bajando": "Keep scrolling",
"Un jugador": "Single player",
"Español, inglés, alemán, francés e italiano": "English, Spanish, German, French, Italian",
"Fecha por anunciar": "Release date TBA",
"cartas": "cards",
"sets": "sets",
"actos": "acts",
"barrios que se andan": "walkable districts",
"idiomas": "languages",
"De que te timen a poner tu nombre en una persiana":
    "From being ripped off to your name on a shutter",
"El problema: no sabes lo que tienes": "The problem: you don't know what you have",
"La solución: tasar antes de vender": "The fix: appraise before you sell",
"La acción: la persiana de la esquina": "The move: the shutter on the corner",
"Una de las 540": "One of the 540",
"Pasa el ratón por encima": "Move your pointer over it",
"Miko del Dios Dragón": "Miko of the Dragon God",
"Embestida del Farol": "Lantern Charge",
"Evolución": "Evolution",
"Debilidad · Luz ×2": "Weakness · Light ×2",
"Lo que hay dentro": "What's in it",
"Se alquila": "To let",
"Ponle tu nombre a la persiana": "Put your name on that shutter",
"Añádelo a tu lista de deseados y te enteras el día que abra.":
    "Add it to your wishlist and you'll hear the day it opens.",
"540 cartas, y todas significan algo": "540 cards, and all of them mean something",
"Un mercado que se mueve solo": "A market that moves on its own",
"Trueque cara a cara": "Trading, face to face",
"Un duelo de verdad": "An actual card game",
"Un vecindario que se anda": "A neighbourhood you walk",
"Una campaña con final": "A campaign with an ending",
"En qué anda el desarrollo. Lo último, arriba.":
    "What development is up to. Newest first.",
"Del juego en marcha, sin retocar. Púlsalas para verlas grandes.":
    "Straight from the running game, unretouched. Click for the full size.",
"Las novedades necesitan JavaScript. Sin él, el resto de la página se lee igual.":
    "The news list needs JavaScript. Without it, the rest of the page reads the same.",
"Un juego de <strong>Ryujindo Games</strong>, en desarrollo.":
    "A game by <strong>Ryujindo Games</strong>, in development.",
}

# Bloques largos: párrafos enteros, con su sangrado. Se sustituyen aparte para
# que el diccionario de arriba siga siendo legible.
BLOQUES = [
("""      Te compró la carta de tu abuela por una décima parte de lo que valía.
      No te engañó: no sabías lo que tenías. Aprende lo suficiente para que
      no vuelva a pasar.""",
 """      He bought your grandmother's card for a tenth of what it was worth.
      He didn't cheat you: you didn't know what you had. Learn enough that it
      doesn't happen again."""),
("""      No es un juego de reponer estantes. Es un juego de <strong>saber cuánto vale
      lo que tienes delante</strong>, y de decidir a quién se lo vendes.""",
 """      This isn't a game about restocking shelves. It's a game about <strong>knowing
      what the thing in front of you is worth</strong> — and deciding who you sell it to."""),
("""            Amanece en el cuarto de seis tatamis que te presta tu abuela, con la
            mudanza sin abrir y el alquiler venciendo el viernes. En una de esas
            cajas hay una carta que vale mucho más de lo que te van a pagar por ella.""",
 """            Morning in the six-tatami room your grandmother lends you, boxes still
            taped shut and rent due on Friday. One of those boxes holds a card worth a
            great deal more than anyone is about to pay you for it."""),
("""            Kenji te ofrece <strong>¥12.000 en efectivo y sin papeles</strong>. No
            miente, no te presiona y no se disculpa: simplemente sabe algo que tú
            no sabes. Aceptas, porque el viernes es el viernes.""",
 """            Kenji offers <strong>¥12,000, cash, no paperwork</strong>. He doesn't lie,
            he doesn't push and he doesn't apologise: he simply knows something you
            don't. You take it, because Friday is Friday."""),
("""            El precio de una carta no es un número: lo mueven la conservación, el
            foil, el índice del set y el torneo del domingo, que sube un 35 % el
            elemento que gane. Una tasación cuesta dinero; equivocarse cuesta más.""",
 """            A card's price isn't a number: condition, foil, set index and Sunday's
            tournament all move it — the winning element gains 35 %. An appraisal costs
            money; getting it wrong costs more."""),
("""            Y luego está la otra mitad: <strong>cada carta vale una cifra distinta
            según quién te la compre</strong>. El mayorista de la esquina paga el
            55 % y paga hoy. La aplicación paga más y descuenta comisión, envío y
            funda. Un coleccionista de la calle paga de más por lo suyo, y el
            tablón de encargos paga una prima por la pieza exacta que alguien lleva
            semanas buscando.""",
 """            Then there's the other half: <strong>every card is worth a different
            number depending on who buys it</strong>. The wholesaler on the corner pays
            55 % and pays today. The app pays more and takes its cut, plus postage and a
            sleeve. A collector in the street overpays for his own set, and the request
            board pays a premium for the exact card somebody has spent weeks hunting."""),
("""            El <strong>貸店舗</strong> está a la vista desde el primer día: un local
            vacío con la persiana echada y un cartel de «se alquila». Cuatro actos
            —el cuarto, el alquiler, las convenciones y el traspaso— separan una
            cosa de la otra.""",
 """            The <strong>貸店舗</strong> is in plain sight from day one: an empty unit,
            shutter down, "to let" sign in the window. Four acts — the room, the rent,
            the conventions and the lease — stand between one and the other."""),
("""            Y no estás solo en la cola: hay un vecino ahorrando para el mismo local
            a su propio ritmo. Si firma antes que tú, el precio sube un 15 % para
            siempre.""",
 """            And you're not alone in the queue: a neighbour is saving for that same
            unit at his own pace. If he signs first, the price goes up 15 % for good."""),
("""      Cada carta tiene elemento, vitalidad, ataque y la debilidad que la tumba —
      y un precio que depende de todo eso más la conservación, el foil y lo que
      pasara el domingo. Muévela.""",
 """      Every card has an element, health, an attack and the weakness that takes it
      down — and a price that depends on all of that plus condition, foil and whatever
      happened on Sunday. Move it around."""),
("""      Seis sistemas que se tocan entre sí, y ninguno es un menú con un botón.""",
 """      Six systems that touch each other, and not one of them is a menu with a button."""),
("""      Está en tu misma calle desde el primer día, con la persiana echada y la
      marquesina encendida. Cuatro actos después, el nombre del cristal es el tuyo.""",
 """      It's on your own street from day one, shutter down and the awning lit. Four
      acts later, the name on the glass is yours."""),
("""          Seis sets de noventa, cada una con su elemento, su vitalidad, su ataque
          y la debilidad que la tumba. Salen de un catálogo determinista: la
          090/090 del set 龍神 es la misma carta en tu partida y en la de
          cualquiera.""",
 """          Six sets of ninety, each card with its element, its health, its attack and
          the weakness that takes it down. They come from a deterministic catalogue:
          090/090 of the 龍神 set is the same card in your game as in anyone else's."""),
("""          El torneo del domingo sube un elemento entero un 35 %, y eso reordena
          media colección mientras duermes. Comprar barato el sábado lo que sube
          el domingo es una jugada — si sabes quién va a ganar.""",
 """          Sunday's tournament lifts a whole element by 35 %, and that reshuffles half
          your collection while you sleep. Buying cheap on Saturday what rises on Sunday
          is a play — if you know who's going to win."""),
("""          En el mercadillo del sábado se cambia con gente que tasa por rareza y se
          salta el meta. Ahí está el margen — y el que tienes delante también
          tiene ojo, y se acuerda de ti la próxima vez.""",
 """          At Saturday's market you trade with people who value by rarity and ignore
          the meta. That's where the margin is — and the person across the table has an
          eye too, and remembers you next time."""),
("""          <b>一本勝負</b>: mazos de veinte cartas, tres copias como máximo, y nunca
          más de las que tengas de verdad en la carpeta. Se juega en las mesas de
          tu tienda y en el torneo del domingo.""",
 """          <b>一本勝負</b>: twenty-card decks, three copies maximum, and never more
          copies than you really own. Played on your shop's tables and at the Sunday
          tournament."""),
("""          中野, アメ横 y 秋葉原, el pasaje comercial, el cruce, la estación con su
          andén, un parque con cerezos y un barrio de casas donde no se vende
          nada. Se va de una punta a otra andando.""",
 """          Nakano, Ameyoko and Akihabara, the covered arcade, the crossing, the station
          and its platform, a park with cherry trees, and a residential street where
          nothing is for sale. You walk from one end to the other."""),
("""          Cuatro actos, del cuarto de la mudanza a la firma del traspaso, con un
          hilo de mensajes que ata unos con otros. Hay un final, y se puede llegar
          a él.""",
 """          Four acts, from the room full of moving boxes to signing the lease, with a
          thread of messages tying them together. There is an ending, and you can reach
          it."""),
("""        Las capturas son del juego en marcha y corresponden a una versión en
        desarrollo: lo que se ve aquí puede cambiar.""",
 """        Screenshots are from the running game and show a build in development:
        what you see here may change."""),
]

# Pies de foto y textos alternativos: pares cortos, uno por línea.
PIES = {
"<b>El cruce</b>Se cruza andando, con el resto del barrio al otro lado.":
    "<b>The crossing</b>You cross it on foot, with the rest of the neighbourhood on the other side.",
"<b>Abrir un sobre</b>Cinco cartas de una en una. Abrirlo suele ser peor negocio que venderlo cerrado, y está calculado para que lo sea.":
    "<b>Opening a pack</b>Five cards, one at a time. Opening it is usually worse business than selling it sealed, and it's balanced to be.",
"<b>La ficha</b>Conservación, índice del set, debilidad y la horquilla de precio — si has pagado por tasarla.":
    "<b>The card panel</b>Condition, set index, weakness — and a price range, if you paid to have it appraised.",
"<b>一本勝負</b>Activos, banquillo, mano y 気. Se juega con las cartas que tienes.":
    "<b>一本勝負</b>Active, bench, hand and 気. You play with the cards you actually have.",
"<b>La criba</b>Ordenar, tasar y decidir por dónde sale cada carta. Es donde se gana o se pierde el día.":
    "<b>Sorting the haul</b>Sort, appraise, and decide where each card goes out. This is where the day is won or lost.",
"<b>貸店舗</b>La meta, visible desde el primer día y en la misma calle en la que duermes.":
    "<b>貸店舗</b>The goal, in plain sight from day one and on the same street you sleep on.",
"<b>El 横丁</b>Dos metros y medio de ancho, farolillos y una raja de cielo.":
    "<b>The 横丁</b>Two and a half metres wide, lanterns overhead and a slot of sky.",
"<b>秋葉原</b>La avenida de los rótulos, y la tienda de sueltas al fondo del callejón.":
    "<b>Akihabara</b>The avenue of signs, with the singles shop at the end of the back alley.",
"<b>El parque</b>Un torii, dos cerezos y un altar. No se vende nada aquí, y hace falta.":
    "<b>The park</b>A torii, two cherry trees and a small shrine. Nothing is for sale here, and it's needed.",
"<b>El ramen del callejón</b>Seis taburetes y una barra, en un local que es un tramo del pasaje.":
    "<b>The ramen place</b>Six stools and a counter, in a unit that is one stretch of the alley.",
"<b>Kenji</b>Nunca miente y nunca se disculpa. Con el tiempo, deja de ser el que te timó.":
    "<b>Kenji</b>He never lies and never apologises. In time, he stops being the man who ripped you off.",
"Un cruce de peatones con rótulos de neón, coches parados y gente esperando":
    "A pedestrian crossing with neon signs, stopped cars and people waiting",
"Cinco cartas abiertas en abanico sobre un tapete oscuro":
    "Five cards fanned out on a dark playmat",
"La ficha de una carta con su nombre, ataque y multiplicadores, sobre la vista de la colección":
    "A card's detail panel showing its name, attack and multipliers over the collection view",
"El tablero de duelo con las cartas activas, el banquillo y la mano":
    "The duel board with active cards, bench and hand",
"El panel de la carpeta con la lista de cartas ordenadas":
    "The binder panel listing sorted cards",
"Un callejón estrecho con farolillos rojos encendidos":
    "A narrow alley strung with lit red lanterns",
"Una avenida con rótulos verticales y torres iluminadas":
    "An avenue of vertical signs and lit towers",
"Un torii rojo entre cerezos con pétalos en el suelo":
    "A red torii among cherry trees with petals on the ground",
"La barra de un local de ramen con seis taburetes":
    "A ramen counter with six stools",
"Kenji detrás de su mostrador durante una conversación":
    "Kenji behind his counter during a conversation",
"Kenji, detrás de su mostrador, ofreciendo doce mil yenes por la carta":
    "Kenji, behind his counter, offering twelve thousand yen for the card",
"La carpeta con las cartas ordenadas y sus precios por canal":
    "The binder with cards sorted and their price in each channel",
"El local vacío con la persiana echada y el cartel de se alquila":
    "The empty shop unit with its shutter down and a to-let sign",
"龍神ノ巫女, Miko del Dios Dragón, carta secreta del set Ryūjin":
    "龍神ノ巫女, Miko of the Dragon God, secret card from the Ryūjin set",
}

# Palabras que solo existen en español: si sobrevive alguna, es que falta una
# entrada en el diccionario. No es una gramática, es un detector de olvidos.
DELATORAS = r"\b(el|la|los|las|una|unos|del|por|para|con|que|más|cuando|desde|tienes|juego|tienda|cartas|precio|dinero)\b"


def main():
    seco = "--seco" in sys.argv
    s = io.open(os.path.join(AQUI, "index.html"), encoding="utf-8").read()

    for a, b in ESTRUCTURA:
        s = s.replace(a, b)
    for a, b in BLOQUES:
        if a not in s:
            print("  ⚠ bloque no encontrado (¿cambió el español?): %s…" % a.strip()[:56])
        s = s.replace(a, b)
    for a, b in sorted(list(TEXTOS.items()) + list(PIES.items()),
                       key=lambda kv: -len(kv[0])):     # los largos primero
        s = s.replace(">" + a + "<", ">" + b + "<")
        s = s.replace('"' + a + '"', '"' + b + '"')
        s = s.replace(a, b)

    # ¿Ha sobrevivido español?
    texto = re.sub(r"<[^>]+>", " ", s)
    texto = re.sub(r"<!--.*?-->", " ", texto, flags=re.S)
    restos = sorted(set(m.group(0).lower() for m in re.finditer(DELATORAS, texto, re.I)))

    if seco:
        print("en seco · %d líneas" % len(s.splitlines()))
    else:
        io.open(os.path.join(AQUI, "en", "index.html"), "w", encoding="utf-8").write(s)
        print("en/index.html reescrito · %d líneas" % len(s.splitlines()))

    if restos:
        print("\nqueda texto que parece español — falta traducir algo:")
        print("  " + ", ".join(restos))
        sys.exit(1)
    print("sin restos en español.")


if __name__ == "__main__":
    main()
