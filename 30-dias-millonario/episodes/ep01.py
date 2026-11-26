# -*- coding: utf-8 -*-
"""Capítulo 1 / 30 — "No llegarás a nada". Duración objetivo: ~60 s.

Eventos: ("say", personaje, texto) | ("pause", s) | ("sfx", nombre)
Opciones de escena: pre, post, min (segundos).
"""
EPISODE = {"num": 1, "title": "NO LLEGARÁS A NADA", "money": 0}

SCENES = [
    {"id": "flash", "pre": 0.0, "post": 0.15, "events": [
        ("sfx", "boom"), ("sfx", "cash"),
        ("say", "LEO", "¡Un millón de euros! ¡Con quince años!", {"exag": 1.0, "cfg": 0.4}),
    ]},
    {"id": "freeze", "pre": 0.0, "post": 0.1, "events": [
        ("sfx", "scratch"),
        ("say", "LEO", "Vale, espera.", {"exag": 0.6}),
    ]},
    {"id": "rewind", "pre": 0.0, "post": 0.1, "min": 1.6, "events": [
        ("sfx", "rewind"),
        ("say", "LEO", "Vamos a rebobinar un poco.", {"exag": 0.6}),
    ]},
    {"id": "hook", "pre": 0.15, "post": 0.3, "events": [
        ("sfx", "stamp", 0.9), ("sfx", "stamp", 1.5), ("sfx", "stamp", 2.1),
        ("say", "LEO", "Hace treinta días, mi padre me dijo que nunca llegaría a nada.", {"exag": 0.55}),
        ("sfx", "tick"),
        ("say", "LEO", "Así que me puse un reto: treinta días para hacerme millonario.", {"exag": 0.75}),
    ]},
    {"id": "title", "pre": 0.1, "post": 0.0, "min": 2.6, "events": [
        ("sfx", "boom"),
    ]},
    {"id": "kitchen", "pre": 0.7, "post": 0.5, "events": [
        ("sfx", "paper"),
        ("say", "PAPA", "¿Un dos? ¿En historia? ¿Otra vez, Leo?", {"exag": 0.85}),
        ("sfx", "thunder"),
        ("say", "MAMA", "Cariño, si no estudias, no vas a llegar a nada en la vida.", {"exag": 0.65}),
        ("say", "PAPA", "Así vas a acabar sin futuro. Te lo digo en serio.", {"exag": 0.8}),
        ("pause", 0.5),
        ("say", "LEO", "¿Y si os demuestro que os equivocáis?", {"exag": 0.7}),
        ("say", "PAPA", "¿Tú? ¿Con estas notas?", {"exag": 0.85}),
        ("sfx", "door"),
    ]},
    {"id": "bedroom", "pre": 0.7, "post": 0.3, "events": [
        ("say", "LEO", "Esa noche no pude dormir.", {"exag": 0.4}),
        ("say", "LEO", "Yo no suspendo porque sea tonto. Suspendo porque estudiar es aburridísimo."),
        ("pause", 0.2),
        ("sfx", "idea"),
        ("say", "LEO", "¿Y si existiera una app que convirtiera tus apuntes en un juego?", {"exag": 0.8}),
    ]},
    {"id": "logo", "pre": 0.2, "post": 0.3, "min": 3.0, "events": [
        ("sfx", "whoosh"),
        ("say", "LEO", "La llamé... ApruebaYa.", {"exag": 0.7}),
        ("sfx", "pop"),
    ]},
    {"id": "plan", "pre": 0.4, "post": 0.4, "events": [
        ("sfx", "camera", 1.35),
        ("say", "LEO", "Le sacas una foto a tus apuntes, y la inteligencia artificial te crea un juego de preguntas en cinco minutos."),
        ("sfx", "pop"),
        ("say", "LEO", "Con puntos, rachas, y competición contra tus amigos.", {"exag": 0.7}),
        ("sfx", "cash"),
        ("say", "LEO", "Si funciona, en treinta días seré millonario.", {"exag": 0.85}),
    ]},
    {"id": "cliff", "pre": 0.3, "post": 1.6, "min": 6.0, "events": [
        ("say", "LEO", "Solo había un problema...", {"exag": 0.5}),
        ("pause", 0.35),
        ("sfx", "boom"),
        ("say", "LEO", "No sé programar.", {"exag": 0.9}),
    ]},
]
