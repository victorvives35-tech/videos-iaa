# BEYOND MIND — "Nobody Is Coming" (vertical motivational short)

`BEYOND_MIND_final.mp4` — 1080×1920 (9:16), 35.5 s, 30 fps, H.264/AAC, −14 LUFS.

Pipeline (fully reproducible, no stock assets):
1. `tts.py <kokoro_dir>` – deep male voice-over (Kokoro TTS, voice `am_onyx`) from `script.json`
2. `assemble_vo.py` – trims and places the lines tightly (no dead air)
3. `align.py` – word timestamps (faster-whisper) for synced subtitles
4. `music.py` – original procedural cinematic score (D minor, builds to a climax, impacts on cuts)
5. `render.py` – procedural cinematic shots (`scenes.py`, `fx.py`), black & gold grade, grain, bloom,
   flash/zoom transitions, karaoke-style animated subtitles, BEYOND MIND end card
6. ffmpeg mix: music side-chain ducked under the voice, loudness normalized
