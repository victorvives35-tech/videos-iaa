#!/usr/bin/env bash
# Montaje final: concatena planos, escala a 1080p, etalonaje, subtítulos ASS y mezcla de audio.
set -euo pipefail
: "${WORK:?define WORK}"
OUT="${OUT:-$(cd "$(dirname "$0")/.." && pwd)/output/GTA6_20_detalles.mp4}"
mkdir -p "$(dirname "$OUT")"
cd "$WORK"
ffmpeg -v error -stats -y -f concat -safe 0 -i concat.txt -i mezcla.wav -filter_complex \
 "[0:v]scale=1920:1080:flags=lanczos,unsharp=5:5:0.5,eq=contrast=1.05:saturation=1.08,vignette=PI/5,noise=alls=4:allf=t,ass=subs.ass:fontsdir=fonts,format=yuv420p[v];[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]" \
 -map "[v]" -map "[a]" -r 30 -c:v libx264 -preset medium -crf 20 -threads 4 \
 -c:a aac -b:a 192k -movflags +faststart -shortest "$OUT"
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height "$OUT"
