# NADIE VA A VENIR A SALVARTE — vídeo motivacional largo (~9:45)

Vídeo cinematográfico estilo "mindset" en español: narración grave, capítulos, tipografía con revelado palabra a palabra, fondos animados (niebla, rayos de luz, brasas, lluvia, estrellas, amanecer), banda sonora sintetizada con impactos en cada capítulo y percusión épica en la segunda mitad.

## Archivos
- `guion.py` — guion completo (texto narrado, texto en pantalla, fondo de cada frase)
- `voz.py` — narración con Piper TTS (voz `es_ES-davefx-medium`) + procesado + `timeline.json`
- `musica.py` — banda sonora generada y sincronizada con la línea de tiempo
- `render.py` — render 1920x1080 @30fps (`--stills t1 t2…` para fotogramas, `--preview ini fin` para un trozo)
- `final.py` — mezcla (ducking de música bajo la voz, -14 LUFS), montaje, SRT, capítulos y miniatura
- `salida/` — miniatura, subtítulos y metadatos de YouTube (el MP4 no se sube a git por tamaño)

## Regenerar
```bash
B=build
python3 voz.py $B && python3 musica.py $B && python3 render.py $B 4 && python3 final.py $B salida
```
Requisitos: `pip install piper-tts opencv-python-headless scipy pillow numpy`, ffmpeg, fuentes Anton y Cormorant Garamond en `/opt/fonts`, voz Piper en `/opt/piper`.

Para cambiar la voz por una de ElevenLabs basta con sustituir la síntesis en `voz.py` (el resto del pipeline se adapta solo a las nuevas duraciones).
