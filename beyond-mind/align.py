# Word timings: Whisper timestamps mapped onto the exact script words (fallback: proportional).
import json, re, numpy as np, soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
lines = json.load(open('build/lines.json'))
a, sr = sf.read('build/vo_raw.wav'); a = resample_poly(a, 2, 3).astype(np.float32)
m = WhisperModel('base.en', device='cpu', compute_type='int8')
segs, _ = m.transcribe(a, word_timestamps=True, language='en')
WW = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
out = []
for L in lines:
    words = L['text'].split()
    cand = [w for w in WW if L['start']-0.25 <= w[1] < L['end']]
    if len(cand) == len(words):
        ts = [(max(c[1], L['start']), min(c[2], L['end'])) for c in cand]; how='whisper'
    else:
        wts = np.array([len(re.sub(r'\W','',w))+2 for w in words], float)
        edges = L['start'] + np.concatenate([[0], np.cumsum(wts)]) / wts.sum() * (L['end']-L['start'])
        ts = list(zip(edges[:-1], edges[1:])); how=f'proportional ({len(cand)} vs {len(words)})'
    print(L['i'], how)
    for w, (s, e) in zip(words, ts): out.append({'line': L['i'], 'w': w, 's': round(s,3), 'e': round(e,3)})
json.dump(out, open('build/words.json','w'), indent=0)
