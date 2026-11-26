# -*- coding: utf-8 -*-
"""Capítulo 1 / 30 — "No llegarás a nada". Duración objetivo: ~60 s.

Eventos: ("say", personaje, texto) | ("pause", s) | ("sfx", nombre)
Opciones de escena: pre, post, min (segundos).
"""
EPISODE = {"num": 1, "title": "NO LLEGARÁS A NADA", "money": 0}

SCENES = [
    {"id": "hook", "pre": 0.5, "post": 0.3, "events": [
        ("sfx", "riser"),
        ("say", "LEO", "Mi padre dice que nunca llegaré a nada."),
        ("say", "LEO", "Tengo treinta días para demostrarle que se equivoca."),
        ("sfx", "cash"),
        ("say", "LEO", "Objetivo: un millón de euros."),
    ]},
    {"id": "title", "pre": 0.1, "post": 0.0, "min": 2.6, "events": [
        ("sfx", "boom"),
    ]},
    {"id": "kitchen", "pre": 0.7, "post": 0.5, "events": [
        ("sfx", "paper"),
        ("say", "PAPA", "¿Un dos en historia, Leo? ¿Otra vez?"),
        ("sfx", "thunder"),
        ("say", "MAMA", "Cariño, si no estudias, no vas a llegar a nada en la vida."),
        ("say", "PAPA", "Así vas a acabar sin futuro. Te lo digo en serio."),
        ("pause", 0.5),
        ("say", "LEO", "¿Y si os demuestro que os equivocáis?"),
        ("say", "PAPA", "¿Tú? ¿Con estas notas?"),
        ("sfx", "door"),
    ]},
    {"id": "bedroom", "pre": 0.7, "post": 0.3, "events": [
        ("say", "LEO", "Esa noche no pude dormir."),
        ("say", "LEO", "Yo no suspendo porque sea tonto. Suspendo porque estudiar es aburridísimo."),
        ("pause", 0.2),
        ("sfx", "idea"),
        ("say", "LEO", "¿Y si existiera una app que convirtiera tus apuntes en un juego?"),
    ]},
    {"id": "logo", "pre": 0.2, "post": 0.3, "min": 3.0, "events": [
        ("sfx", "whoosh"),
        ("say", "LEO", "La llamé... ApruebaYa."),
        ("sfx", "pop"),
    ]},
    {"id": "plan", "pre": 0.4, "post": 0.4, "events": [
        ("sfx", "camera", 1.35),
        ("say", "LEO", "Le sacas una foto a tus apuntes, y la inteligencia artificial te crea un juego de preguntas en cinco minutos."),
        ("sfx", "pop"),
        ("say", "LEO", "Con puntos, rachas, y competición contra tus amigos."),
        ("sfx", "cash"),
        ("say", "LEO", "Si funciona, en treinta días seré millonario."),
    ]},
    {"id": "cliff", "pre": 0.3, "post": 1.6, "min": 6.0, "events": [
        ("say", "LEO", "Solo había un problema..."),
        ("pause", 0.35),
        ("sfx", "boom"),
        ("say", "LEO", "No sé programar."),
    ]},
]
