# 30 DÍAS PARA SER MILLONARIO — serie de 30 capítulos

Leo, 15 años, saca malas notas. Sus padres le dicen que no llegará a nada si no estudia.
Él decide crear **ApruebaYa**, una app que convierte tus apuntes en un juego con IA, para ser
millonario en 30 días. Un capítulo por día (~1 min, vertical 1080×1920 para TikTok/Reels/Shorts).

| Cap. | Título | Estado |
|---|---|---|
| 1 | No llegarás a nada | ✅ `output/ep01_30_dias_millonario.mp4` |
| 2 | Aprender a programar en 24 horas | pendiente |

## Cómo se genera
Todo es procedural (sin imágenes externas):
- `episodes/epXX.py` – guion (diálogos, pausas, efectos)
- `episodes/epXX_vis.py` – escenas animadas (skia)
- `tts.py` – voces con Kokoro TTS (mezcla de estilos + transposición por personaje) → `build/epXX/`
- `audio.py` – música procedural, efectos y mezcla con ducking (-14 LUFS)
- `engine.py` – personajes vectoriales con sincronía labial, subtítulos karaoke, HUD de la serie
- `render.py` – render multiproceso → `output/`

```bash
pip install kokoro-onnx soundfile skia-python scipy numpy pillow
# modelos en ~/kokoro: kokoro-v1.0.onnx (como kokoro.onnx) y voices-v1.0.bin
python3 tts.py ep01 && python3 audio.py ep01 && python3 render.py ep01
python3 render.py ep01 --preview 5 20   # fotogramas sueltos para revisar
```
