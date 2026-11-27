# -*- coding: utf-8 -*-
"""Capítulo 1 / 30 — "El trato". Duración objetivo: ~65 s.

Eventos:
  ("say", personaje, texto, {opciones})  opciones: exag (emoción 0.3-1.2), cfg, gap (pausa después, s)
  ("pause", s)
  ("sfx", nombre, desfase_opcional)
Opciones de escena: pre, post, min (segundos).
"""
EPISODE = {"num": 1, "title": "EL TRATO", "money": 0}

SCENES = [
    # ---------- flash-forward: el final primero
    {"id": "flash", "pre": 0.0, "post": 0.2, "events": [
        ("sfx", "boom"), ("sfx", "cash"),
        ("say", "LEO", "¡Un millón de euros! ¡Con quince años!", {"exag": 1.0, "cfg": 0.4}),
    ]},
    {"id": "freeze", "pre": 0.05, "post": 0.25, "events": [
        ("sfx", "scratch"),
        ("say", "LEO", "Vale... espera.", {"exag": 0.55}),
    ]},
    {"id": "rewind", "pre": 0.0, "post": 0.15, "min": 1.7, "events": [
        ("sfx", "rewind"),
        ("say", "LEO", "Vamos a rebobinar un poco.", {"exag": 0.6}),
    ]},
    {"id": "title", "pre": 0.0, "post": 0.0, "min": 2.2, "events": [
        ("sfx", "boom"),
    ]},
    # ---------- la cocina: el boletín y el trato
    {"id": "kitchen", "pre": 1.6, "post": 0.5, "events": [
        ("sfx", "slide", -0.9),
        ("say", "PAPA", "¿Un dos? ¿En historia?", {"exag": 0.8, "gap": 0.7}),
        ("say", "PAPA", "Leo. Mírame.", {"exag": 0.7, "gap": 0.5}),
        ("say", "MAMA", "Cariño... si no estudias, no vas a llegar a nada en la vida.", {"exag": 0.6, "gap": 0.6}),
        ("say", "LEO", "¿Y si os demuestro que os equivocáis?", {"exag": 0.75, "gap": 0.35}),
        ("sfx", "scoff"),
        ("say", "PAPA", "¿Tú? ¿Con estas notas?", {"exag": 0.9, "gap": 0.9}),
        ("sfx", "hit"),
        ("say", "PAPA", "Te doy treinta días. Si no, se acabó el móvil, y academia todo el verano.", {"exag": 0.8, "gap": 0.6}),
        ("say", "LEO", "Vale. Trato hecho.", {"exag": 0.6, "cfg": 0.6, "seed": 77, "gap": 0.2}),
        ("sfx", "handshake"),
        ("pause", 0.9),
    ]},
    # ---------- la habitación: el descubrimiento
    {"id": "bedroom", "pre": 1.0, "post": 0.3, "events": [
        ("say", "LEO", "Esa noche no pude dormir.", {"exag": 0.4, "gap": 0.6}),
        ("sfx", "cards"),
        ("say", "LEO", "Me sé las estadísticas de trescientos futbolistas...", {"exag": 0.6, "gap": 0.35}),
        ("say", "LEO", "pero no me sé cinco fechas de historia.", {"exag": 0.5, "gap": 0.8}),
        ("sfx", "idea"),
        ("say", "LEO", "Y entonces lo entendí.", {"exag": 0.7, "gap": 0.4}),
        ("say", "LEO", "El problema no era yo. Era cómo nos hacen estudiar.", {"exag": 0.75, "gap": 0.45}),
        ("say", "LEO", "¿Y si estudiar fuera un juego?", {"exag": 0.9, "gap": 0.2}),
    ]},
    {"id": "logo", "pre": 0.3, "post": 0.4, "min": 3.0, "events": [
        ("sfx", "whoosh"),
        ("say", "LEO", "Así nació... ApruebaYa.", {"exag": 0.8}),
        ("sfx", "pop", -0.15),
    ]},
    {"id": "plan", "pre": 0.4, "post": 0.4, "events": [
        ("sfx", "camera", 0.9),
        ("say", "LEO", "Haces una foto a tus apuntes, y la inteligencia artificial te monta un juego de preguntas.", {"exag": 0.65, "gap": 0.3}),
        ("sfx", "pop"),
        ("say", "LEO", "Ganas puntos, haces rachas, y retas a tus amigos.", {"exag": 0.75, "gap": 0.45}),
        ("sfx", "cash"),
        ("say", "LEO", "Si funciona, en treinta días seré millonario.", {"exag": 0.9, "gap": 0.2}),
    ]},
    # ---------- cliffhanger
    {"id": "cliff", "pre": 0.5, "post": 2.4, "events": [
        ("say", "LEO", "Solo había un problema...", {"exag": 0.5, "gap": 0.9}),
        ("sfx", "boom"),
        ("say", "LEO", "No sé programar.", {"exag": 0.8, "gap": 1.1}),
        ("sfx", "whoosh"),
        ("say", "LEO", "Bueno... todavía.", {"exag": 0.7, "gap": 0.2}),
    ]},
]
