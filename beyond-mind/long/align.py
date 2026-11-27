# Per-line Whisper word timestamps mapped onto the exact script words (proportional fallback).
import json, re, numpy as np, soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
TL = json.load(open('build/timeline.json'))
a, sr = sf.read('build/vo_raw.wav')
m = WhisperModel('base.en', device='cpu', compute_type='int8')
out = []; nw = nf = 0
lines = [i for i in TL['items'] if i['type'] == 'line']
for li, L in enumerate(lines):
    seg = a[int(L['start'] * sr): int(L['end'] * sr)]
    seg = resample_poly(seg, 2, 3).astype(np.float32)
    segs, _ = m.transcribe(seg, word_timestamps=True, language='en', beam_size=1)
    cand = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
    words = L['text'].split()
    if len(cand) == len(words):
        ts = [(L['start'] + c[1], L['start'] + c[2]) for c in cand]; nw += 1
    else:
        wts = np.array([len(re.sub(r'\W', '', w)) + 2 for w in words], float)
        e = L['start'] + np.concatenate([[0], np.cumsum(wts)]) / wts.sum() * (L['end'] - L['start'])
        ts = list(zip(e[:-1], e[1:])); nf += 1
    for w, (s, e_) in zip(words, ts):
        out.append({'line': li, 'w': w, 's': round(float(s), 3), 'e': round(float(min(e_, L['end'])), 3)})
json.dump(out, open('build/words.json', 'w'))
print('whisper', nw, 'fallback', nf)
