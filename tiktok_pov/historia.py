# -*- coding: utf-8 -*-
"""Historia original en formato POV animado (vertical) — Parte 1."""

TITULO = "POV: el último bus de la noche se salta tu parada"

# (personaje, escena, texto)  personajes: N = narrador (tú), C = conductor, G = chica, A = altavoz
LINEAS = [
    ("N", "stop", "Eran las doce y cuarto, y yo era el único esperando el último bus de la noche."),
    ("N", "arrive", "Cuando por fin llegó, el conductor ni me miró. Solo dijo una cosa."),
    ("C", "driver", "Siéntate al fondo. Y no te levantes hasta que yo te lo diga."),
    ("N", "aisle", "Raro. Pero estaba demasiado cansado para discutir."),
    ("N", "girl", "Al fondo había una chica con la capucha puesta. Me hizo una señal para que me sentara a su lado."),
    ("G", "both", "¿Es tu primera vez en esta línea?"),
    ("N", "both_pale", "Le dije que sí. Y se quedó pálida."),
    ("G", "both_pale", "Entonces escúchame bien. Pase lo que pase, no digas tu nombre en voz alta."),
    ("N", "window", "Pensé que era una broma. Hasta que vi por la ventana cómo mi parada pasaba de largo."),
    ("N", "grab", "Me levanté para avisar al conductor, y la chica me agarró del brazo."),
    ("G", "grab", "Te ha dicho que no te levantes."),
    ("N", "flicker", "Las luces empezaron a parpadear. Y por los altavoces sonó una voz."),
    ("A", "speaker", "Próxima parada. La casa de Marcos."),
    ("N", "shock", "Marcos soy yo. Y yo no le había dicho mi nombre a nadie."),
    ("N", "end", "¿Quieres la parte dos? Comenta y te la traigo."),
]

VOCES = {"N": ("em_alex", 1.0), "C": ("em_santa", 0.88), "G": ("ef_dora", 1.0), "A": ("em_santa", 0.8)}
