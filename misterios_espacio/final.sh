#!/usr/bin/env bash
# Montaje final: une secciones, aplica etalonaje, subtítulos y audio, y exporta MP4 para YouTube.
set -euo pipefail
: "${WORK:?define WORK}"
OUT="${OUT:-$(cd "$(dirname "$0")/.." && pwd)/output/10_misterios_del_espacio.mp4}"
mkdir -p "$(dirname "$OUT")"
cd "$WORK"
ffmpeg -v error -stats -y -f concat -safe 0 -i concat.txt -i mezcla.wav -filter_complex \
 "[0:v]eq=contrast=1.04:saturation=1.06,vignette=PI/6,noise=alls=3:allf=t,ass=subs.ass:fontsdir=fonts,format=yuv420p[v];[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]" \
 -map "[v]" -map "[a]" -r 30 -c:v libx264 -preset medium -crf 21 -maxrate 14M -bufsize 20M -threads 4 \
 -c:a aac -b:a 192k -movflags +faststart -shortest "$OUT"
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height "$OUT"
