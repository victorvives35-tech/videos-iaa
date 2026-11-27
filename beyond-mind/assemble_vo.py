# Trim each TTS line, place on a timeline with tight gaps, export vo_raw.wav + line timings.
import json, numpy as np, soundfile as sf
lines = json.load(open('script.json'))
SR = 24000
START = 0.15                       # voice starts almost instantly (hook)
GAPS = [0.18,0.22,0.12,0.25,0.22,0.22,0.25,0.22,0.3,0.35,0.15,0.9]  # gap after line i
out, t, timing = [], START, []
for i, _ in enumerate(lines):
    a, sr = sf.read(f'build/vo_{i:02d}.wav'); assert sr == SR
    env = np.abs(a) > 0.01
    idx = np.where(env)[0]; s, e = max(idx[0]-240, 0), min(idx[-1]+1200, len(a))
    a = a[s:e]
    timing.append({'i': i, 'text': lines[i], 'start': t, 'end': t+len(a)/SR})
    out.append((t, a)); t += len(a)/SR + (GAPS[i] if i < len(GAPS) else 0)
total = t + 0.2
buf = np.zeros(int((total)*SR)+SR)
for st, a in out:
    k = int(st*SR); buf[k:k+len(a)] += a
sf.write('build/vo_raw.wav', buf[:int(total*SR)], SR)
json.dump(timing, open('build/lines.json','w'), indent=1)
print('voice ends at', round(total,2))
for x in timing: print(round(x['start'],2), round(x['end'],2), x['text'])
