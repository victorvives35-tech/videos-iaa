"""Render BEYOND MIND: scenes + grade + transitions + animated subtitles -> build/video.mp4
usage: python3 render.py [--stills t1,t2,...] [--from s --to e]"""
import sys, json, math, subprocess, numpy as np, cv2
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont
import scenes as S
from fx import W, H, FPS, grade, grain, cam

DUR = 35.5
CUTS = [(0.0, 'Storm'), (2.27, 'Hourglass'), (4.5, 'City'), (6.1, 'Climber'), (8.5, 'Boxer'), (11.1, 'Runner'),
        (13.5, 'Lifter'), (14.95, 'Timelapse'), (16.3, 'Mind'), (19.1, 'Sprint'), (19.95, 'Sparks'), (20.6, 'King'),
        (21.4, 'Penthouse'), (23.2, 'Trails'), (24.9, 'Door'), (26.8, 'Summit'), (28.7, 'EndCard')]
END_CARD = 28.7
WORDS = json.load(open('build/words.json'))
GOLD_WORDS = {'NOBODY', 'SAVE', 'TOMORROW.', 'BUILD.', 'ONE', 'MORE', 'STEP.', 'DISCIPLINE', 'HABITS', 'STAY.', 'REPEAT.',
              'EVERY', 'MIND', 'QUIT', 'TRAIN', 'SHARPEN', 'OWN', 'DISCOMFORT.', 'READY.', 'NEVER', 'STOPS.'}

# ---- subtitle chunks: 1-3 words, max ~15 chars ----
CHUNKS = []
for li in sorted({w['line'] for w in WORDS}):
    if li == 12: continue
    ws = [w for w in WORDS if w['line'] == li]
    cur = []
    for w in ws:
        cand = cur + [w]
        txt = ' '.join(x['w'] for x in cand)
        if cur and (len(txt) > 15 or len(cand) > 3 or cur[-1]['w'][-1] in '.,'):
            CHUNKS.append(cur); cur = [w]
        else:
            cur = cand
    if cur: CHUNKS.append(cur)
for i, c in enumerate(CHUNKS):
    nxt = CHUNKS[i + 1][0]['s'] if i + 1 < len(CHUNKS) else c[-1]['e'] + 0.3
    c_end = min(nxt, c[-1]['e'] + 0.45)
    CHUNKS[i] = dict(words=c, start=c[0]['s'] - 0.04, end=c_end)

_fonts = {}
def font(sz):
    if sz not in _fonts: _fonts[sz] = ImageFont.truetype('fonts/Anton-Regular.ttf', sz)
    return _fonts[sz]


def subtitle_layer(t):
    """returns RGBA float overlay or None"""
    if t >= END_CARD - 0.05: return None
    ch = next((c for c in CHUNKS if c['start'] <= t < c['end']), None)
    if ch is None: return None
    hook = ch['words'][0]['line'] == 0
    base = 150 if hook else 128
    words = [w['w'].upper() for w in ch['words']]
    f = font(base)
    space = int(base * 0.28)
    widths = [f.getbbox(w)[2] for w in words]
    # wrap if too wide
    rows, cur, cw = [], [], 0
    for i, w in enumerate(widths):
        if cur and cw + space + w > W - 140: rows.append(cur); cur, cw = [], 0
        cur.append(i); cw += (space if len(cur) > 1 else 0) + w
    rows.append(cur)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(im); ds = ImageDraw.Draw(sh)
    lh = int(base * 1.12); y0 = int(H * 0.645) - (len(rows) * lh) // 2
    if hook: y0 = int(H * 0.60) - (len(rows) * lh) // 2
    for ri, row in enumerate(rows):
        tw = sum(widths[i] for i in row) + space * (len(row) - 1); x = (W - tw) // 2; y = y0 + ri * lh
        for i in row:
            w = ch['words'][i]; age = t - w['s']
            if age < -0.02: x += widths[i] + space; continue
            k = min(1.0, max(0.0, (age + 0.02) / 0.12))
            sc = 1.0 + 0.35 * (1 - k) ** 2
            fs = int(base * sc); ff = font(fs)
            active = w['s'] - 0.02 <= t < w['e'] + 0.05
            gold = words[i] in GOLD_WORDS
            col = (255, 196, 84) if gold else (255, 255, 255)
            if not active and not gold: col = (238, 232, 222)
            cx = x + widths[i] / 2; bw = ff.getbbox(words[i])[2]
            px = int(cx - bw / 2); py = int(y - (fs - base) * 0.55)
            a = int(255 * k)
            ds.text((px + 6, py + 10), words[i], font=ff, fill=int(200 * k))
            dr.text((px, py), words[i], font=ff, fill=col + (a,), stroke_width=7, stroke_fill=(0, 0, 0, int(230 * k)))
            x += widths[i] + space
    rgba = np.asarray(im).astype(np.float32) / 255
    shadow = cv2.GaussianBlur(np.asarray(sh).astype(np.float32) / 255, (0, 0), 14)
    return rgba, shadow


_inst = {}
def scene(name):
    if name not in _inst: _inst[name] = getattr(S, name)()
    return _inst[name]


def cut_at(t):
    idx = max(i for i, (c, _) in enumerate(CUTS) if c <= t)
    st = CUTS[idx][0]; en = CUTS[idx + 1][0] if idx + 1 < len(CUTS) else DUR
    return idx, st, en


def render_frame(fi):
    t = fi / FPS
    idx, st, en = cut_at(t)
    name = CUTS[idx][1]; lt = t - st; d = en - st
    sc = scene(name)
    if name == 'EndCard':
        tags = [w['s'] - END_CARD for w in WORDS if w['line'] == 12][2:6]
        img = sc.frame(lt, d, tags)
    else:
        img = sc.frame(lt, d)
    img = grade(img, mix=0.8 if name != 'Trails' else 0.65)
    # transition: zoom punch + flash on every cut
    if idx > 0 and lt < 0.3:
        k = math.exp(-lt * 12)
        img = cam(img, 1.0 + 0.09 * k, W / 2, H / 2)
        img = img + np.asarray((1.0, 0.85, 0.6), np.float32) * 0.55 * math.exp(-lt * 22)
    if en - t < 0.08 and idx + 1 < len(CUTS):  # whip out
        k = 1 - (en - t) / 0.08
        img = cv2.blur(img, (1, int(1 + 50 * k)))
    img = grain(img, fi, 0.04)
    sub = subtitle_layer(t)
    if sub:
        rgba, shadow = sub
        img = img * (1 - shadow[..., None] * 0.6)
        a = rgba[..., 3:4]; img = img * (1 - a) + rgba[..., :3] * a
    if t < 0.1: img *= 0.4 + 6 * t
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--stills':
        ts = [float(x) for x in args[1].split(',')]
        with Pool(4) as p: frames = p.map(render_frame, [int(x * FPS) for x in ts])
        thumbs = [cv2.resize(f, (270, 480), interpolation=cv2.INTER_AREA) for f in frames]
        while len(thumbs) % 6: thumbs.append(np.zeros_like(thumbs[0]))
        rows = [np.hstack(thumbs[i:i + 6]) for i in range(0, len(thumbs), 6)]
        Image.fromarray(np.vstack(rows)).save('build/contact.png')
        for x, f in zip(ts, frames): Image.fromarray(f).save(f'build/still_{x:05.2f}.png')
        sys.exit()
    n = int(DUR * FPS)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', 'build/video_only.mp4'],
                          stdin=subprocess.PIPE)
    with Pool(4) as p:
        for i, fr in enumerate(p.imap(render_frame, range(n), chunksize=3)):
            ff.stdin.write(fr.tobytes())
            if i % 60 == 0: print(f'frame {i}/{n}', flush=True)
    ff.stdin.close(); ff.wait()
    print('done')
