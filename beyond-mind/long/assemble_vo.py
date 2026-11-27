# Place trimmed voice lines on a timeline; chapter cards get their own silent beats. Target ~600 s total.
import json, numpy as np, soundfile as sf
SR = 24000; TARGET = 600.4
items = json.load(open('build/items.json'))
clips = []
for it in items:
    if it['type'] == 'line':
        a, _ = sf.read(it['wav']); idx = np.where(np.abs(a) > 0.01)[0]
        clips.append(a[max(idx[0] - 240, 0): idx[-1] + 1200])
CARD = {'@': 3.2, '#': 3.0}; END_TAIL = 6.5; START = 0.15
speech = sum(len(c) for c in clips) / SR
cards = sum(CARD[i['kind']] for i in items if i['type'] == 'card')
nl = len(clips)
gap = (TARGET - START - speech - cards - END_TAIL) / (nl - 1)
print('speech', round(speech, 1), 'gap', round(gap, 3))
t = START; ci = 0; timeline = []
for k, it in enumerate(items):
    if it['type'] == 'card':
        it['start'] = t; it['end'] = t + CARD[it['kind']]; t = it['end']; timeline.append(it); continue
    a = clips[ci]; ci += 1
    it['start'] = t; it['end'] = t + len(a) / SR; it['clip'] = a
    nxt = items[k + 1] if k + 1 < len(items) else None
    g = gap * (1.0 if it['text'].endswith('.') else 0.5)
    if nxt is None: g = 0
    elif nxt['type'] == 'card': g = 0.6
    if nxt is not None and nxt['type'] == 'line' and nxt['text'].startswith('Beyond Mind.'): g = gap + 1.6
    t = it['end'] + g; timeline.append(it)
total = timeline[-1]['end'] + END_TAIL
buf = np.zeros(int(total * SR) + SR)
for it in timeline:
    if it['type'] == 'line':
        k = int(it['start'] * SR); buf[k:k + len(it['clip'])] += it['clip']; del it['clip']
sf.write('build/vo_raw.wav', buf[:int(total * SR)], SR)
json.dump({'total': total, 'items': timeline}, open('build/timeline.json', 'w'), indent=1)
print('total', round(total, 1))
