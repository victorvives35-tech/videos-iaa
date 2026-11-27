# Parse script.txt (# = chapter card, @ = title card) and synthesize every spoken line with Kokoro (am_onyx).
import json, sys, soundfile as sf
from kokoro_onnx import Kokoro
K = sys.argv[1]
k = Kokoro(K + '/model.onnx', K + '/voices.bin')
items = []
for raw in open('script.txt').read().split('\n'):
    l = raw.strip()
    if not l: continue
    if l[0] in '#@':
        if l == '# HOOK': continue
        a, _, b = l[1:].partition('|'); items.append({'type': 'card', 'kind': l[0], 'a': a.strip(), 'b': b.strip()})
    else:
        items.append({'type': 'line', 'text': l})
n = 0
for it in items:
    if it['type'] != 'line': continue
    last = it['text'].startswith('Beyond Mind.')
    a, sr = k.create(it['text'], voice='am_onyx', lang='en-us', speed=0.86 if last else 0.93)
    it['wav'] = f'build/vo_{n:03d}.wav'; sf.write(it['wav'], a, sr); n += 1
json.dump(items, open('build/items.json', 'w'), indent=1)
print(n, 'lines')
