# 30 DÍAS PARA SER MILLONARIO — serie de 30 capítulos

Leo, 15 años, saca malas notas. Sus padres le dicen que no llegará a nada si no estudia.
Él decide crear **ApruebaYa**, una app que convierte tus apuntes en un juego con IA, para ser
millonario en 30 días. Un capítulo por día (~1 min, vertical 1080×1920 para TikTok/Reels/Shorts).

| Cap. | Título | Estado |
|---|---|---|
| 1 | El trato | ✅ `output/ep01_30_dias_millonario.mp4` (66 s) |
| 2 | Aprender a programar en 24 horas | pendiente |

## Cómo se genera
Todo es procedural (sin imágenes externas):
- `episodes/epXX.py` – guion (diálogos, pausas, efectos)
- `episodes/epXX_vis.py` – escenas animadas (skia)
- `tts.py` – voces expresivas con **Chatterbox Multilingual** (emoción por línea). Cada línea se verifica con Whisper y se regenera si no coincide con el guion; se recorta el sobrante final. Timbre de referencia por personaje generado con Kokoro.
- `pauses.py` – inserta silencios reales donde el guion pone "..." (el TTS los ignora)
- `verify_voices.py` – transcribe todas las líneas y marca las dudosas
- `audio.py` – música procedural, efectos y mezcla con ducking (-14 LUFS)
- `engine.py` – personajes vectoriales con sincronía labial, subtítulos karaoke, HUD de la serie
- `render.py` – render multiproceso → `output/`

```bash
pip install chatterbox-tts faster-whisper kokoro-onnx soundfile skia-python scipy numpy pillow
# (necesita acceso a huggingface.co y us.aws.cdn.hf.co para descargar los modelos)
# modelos en ~/kokoro: kokoro-v1.0.onnx (como kokoro.onnx) y voices-v1.0.bin
python3 tts.py ep01 && python3 pauses.py ep01 && python3 tts.py ep01 && python3 audio.py ep01 && python3 render.py ep01
python3 render.py ep01 --preview 5 20   # fotogramas sueltos para revisar
```
