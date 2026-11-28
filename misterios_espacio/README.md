# 10 misterios del espacio — proyecto del documental

| Archivo | Función |
|---|---|
| `guion.py` | Guion con etiquetas: H = dato contrastado, P = hipótesis científica |
| `tts.py` | Narración (Kokoro, voz `em_alex`, 6 % más grave) y línea de tiempo |
| `media.py` | Descarga de imágenes y vídeos de NASA Image and Video Library |
| `cgi.py` | Animaciones científicas propias (agujero negro con lente gravitacional, galaxias, Europa, Titán, gráficos…) |
| `render.py` | Plan de montaje (185 planos: vídeo NASA + imágenes con movimiento + animaciones) y render por secciones |
| `audio.py` | Música ambiental original, efectos y mezcla con ducking bajo la voz |
| `subs.py` | Subtítulos, rótulos de cada misterio, etiquetas DATO CONTRASTADO / HIPÓTESIS, créditos por plano |
| `miniatura.py` | Miniatura 1280x720 |
| `final.sh` | Exportación final MP4 1080p (H.264 + AAC, −14 LUFS) |
| `descripcion_youtube.md`, `capitulos.txt` | Descripción con fuentes, créditos y capítulos |

Orden de ejecución (con `WORK` apuntando a la carpeta de trabajo con `fonts/` y `kokoro/`):
`tts.py → media.py → render.py → audio.py → subs.py → miniatura.py → final.sh`
