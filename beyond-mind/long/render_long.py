"""Render the 10-minute BEYOND MIND film in 30 s segments (resumable).
usage (from beyond-mind/): python3 long/render_long.py plan | stills t1,t2.. | render [seg_from seg_to] | concat"""
import os, sys, json, math, random, subprocess, re, numpy as np, cv2
from collections import OrderedDict
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scenes as S1, scenes2 as S2
from fx import W, H, FPS, grade, grain, cam

B = 'long/build/'
TL = json.load(open(B + 'timeline.json'))
WORDS = json.load(open(B + 'words.json'))
DUR = TL['total']
ITEMS = TL['items']
LINES = [i for i in ITEMS if i['type'] == 'line']
END_START = LINES[-1]['start'] - 1.2
SEG = 30.0

THEMES = [
    (r'clock|time|second|days|weeks|months|years|year ago|running', ['Clock', 'Hourglass', 'Timelapse']),
    (r'alarm|wak|early|morning|bed', ['Alarm', 'Timelapse', 'Runner']),
    (r'train|workout|rep|arms|sweat|body|athlete', ['Lifter', 'Pushups', 'Boxer', 'Sprint']),
    (r'\brun|mile|moving|fast|tortoise', ['Runner', 'Sprint', 'Desert']),
    (r'mountain|top|climb|step|leap|higher|raise', ['Climber', 'Summit', 'Stairs']),
    (r'mind|voice|head|think|focus|doubt|calm|control|attitude|silence', ['Mind', 'Meditate']),
    (r'fire|forge|steel|refined|spark|burn|hottest', ['Embers', 'Sparks']),
    (r'diamond|pressure|unbreakable', ['Diamond', 'Embers']),
    (r'storm|chaos|pain|fail|down|scar|struggle|setback|tired|laugh|doubted|dangerous', ['Storm', 'RainWindow', 'Boxer']),
    (r'success|reward|freedom|respect|world|wealth|luxury|glamorous|outlives', ['Penthouse', 'Trails', 'King']),
    (r'dream|future|potential|becom|version|inside|ready|meet|door|start', ['Door', 'Summit', 'Stairs', 'Ocean']),
    (r'alone|lonely|road|night|dark|quiet', ['Desert', 'RainWindow', 'City', 'Trails']),
    (r'work|build|plan|late|read|page|hour|distraction|scroll', ['Desk', 'City', 'Alarm']),
    (r'peace|steady|patient|wait', ['Meditate', 'Ocean']),
    (r'win|champion|power|great|admire|watch me|best', ['King', 'Summit', 'Penthouse', 'Boxer']),
]
POOL = ['Storm', 'Hourglass', 'City', 'Climber', 'Boxer', 'Runner', 'Lifter', 'Timelapse', 'Mind', 'Sprint', 'Sparks', 'King',
        'Penthouse', 'Trails', 'Door', 'Summit', 'Stairs', 'Meditate', 'Embers', 'Ocean', 'Desert', 'RainWindow', 'Pushups',
        'Diamond', 'Clock', 'Alarm', 'Desk']
NO_MIRROR = {'Alarm'}


def plan():
    rnd = random.Random(7); shots = []; used = {k: 0 for k in POOL}; recent = []
    # opening hook: fixed strong sequence
    for idx, it in enumerate(ITEMS):
        st = it['start'] - (0.08 if it['type'] == 'line' else 0)
        en = ITEMS[idx + 1]['start'] - (0.08 if ITEMS[idx + 1]['type'] == 'line' else 0) if idx + 1 < len(ITEMS) else DUR
        if it['type'] == 'card':
            shots.append(dict(start=st, end=en, scene='Card', args=[it['kind'], it['a'], it['b']])); continue
        if it is LINES[-1] or st >= END_START:
            continue
        en = min(en, END_START)
        if idx == 0: st = 0.0
        n = max(1, round((en - st) / 2.8))
        cand = []
        for pat, sc in THEMES:
            if re.search(pat, it['text'].lower()): cand += sc
        for k in range(n):
            s0 = st + (en - st) * k / n; s1 = st + (en - st) * (k + 1) / n
            opts = [c for c in cand if c not in recent[-4:]] if k < 2 else []
            if not opts:
                opts = sorted([c for c in POOL if c not in recent[-6:]], key=lambda c: (used[c], rnd.random()))[:4]
            if idx == 0 and k == 0: opts = ['Storm']
            c = rnd.choice(opts[:3]); used[c] += 1; recent.append(c)
            args = [rnd.choice([31, 32, 33])] if c == 'City' else []
            shots.append(dict(start=s0, end=s1, scene=c, args=args, t0=rnd.uniform(0, 1.5),
                              mirror=(c not in NO_MIRROR and rnd.random() < 0.4), zdir=rnd.choice([1, -1])))
    shots.append(dict(start=END_START, end=DUR, scene='EndCard', args=[]))
    shots.sort(key=lambda s: s['start'])
    for a, b in zip(shots, shots[1:]): a['end'] = b['start']
    json.dump(shots, open(B + 'shots.json', 'w'), indent=0)
    return shots


GOLD_WORDS = set('''NOBODY SAVE BUILD TODAY NOW CAPABLE TALENT HARD PERFECT CHOICE GROW COMFORT DISCOMFORT DISCIPLINE FIRE FREEDOM
REGRET READY START ACTION WILL GREAT GREATNESS EVERYTHING STEP RELENTLESS CHAMPIONS CONSISTENCY REPEAT DREAM FEAR HABITS FUTURE WORK
IMPOSSIBLE STANDARDS AVERAGE OPPONENT STOP MIND HARD UNBREAKABLE POWER PAIN FOREVER PRICE SACRIFICE FAILURE FOUGHT UP STRONGER
COMEBACK PRESSURE FORGED STRUGGLE ENOUGH PROGRESS NEVER BEYOND MORE MOVING RESULTS LIMITED WORTH DRIVE PLANS'''.split())

CHUNKS = []
for li in range(len(LINES) - 1):
    ws = [w for w in WORDS if w['line'] == li]; cur = []
    for w in ws:
        cand = cur + [w]; txt = ' '.join(x['w'] for x in cand)
        if cur and (len(txt) > 15 or len(cand) > 3 or cur[-1]['w'][-1] in '.,?'):
            CHUNKS.append(cur); cur = [w]
        else: cur = cand
    if cur: CHUNKS.append(cur)
for i, c in enumerate(CHUNKS):
    nxt = CHUNKS[i + 1][0]['s'] if i + 1 < len(CHUNKS) else c[-1]['e'] + 0.3
    CHUNKS[i] = dict(words=c, start=c[0]['s'] - 0.04, end=min(nxt, c[-1]['e'] + 0.45))
CH_STARTS = [c['start'] for c in CHUNKS]
_fonts = {}
def font(sz):
    if sz not in _fonts: _fonts[sz] = ImageFont.truetype('fonts/Anton-Regular.ttf', sz)
    return _fonts[sz]


def subtitle_layer(t):
    if t >= END_START - 0.05: return None
    import bisect
    i = bisect.bisect_right(CH_STARTS, t) - 1
    if i < 0 or not (CHUNKS[i]['start'] <= t < CHUNKS[i]['end']): return None
    ch = CHUNKS[i]; hook = ch['words'][0]['line'] == 0
    base = 150 if hook else 124
    words = [w['w'].upper() for w in ch['words']]
    f = font(base); space = int(base * 0.28)
    widths = [f.getbbox(w)[2] for w in words]
    rows, cur, cw = [], [], 0
    for k, w in enumerate(widths):
        if cur and cw + space + w > W - 140: rows.append(cur); cur, cw = [], 0
        cur.append(k); cw += (space if len(cur) > 1 else 0) + w
    rows.append(cur)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(im); ds = ImageDraw.Draw(sh)
    lh = int(base * 1.12); y0 = int(H * (0.60 if hook else 0.645)) - (len(rows) * lh) // 2
    for ri, row in enumerate(rows):
        tw = sum(widths[k] for k in row) + space * (len(row) - 1); x = (W - tw) // 2; y = y0 + ri * lh
        for k in row:
            w = ch['words'][k]; age = t - w['s']
            if age < -0.02: x += widths[k] + space; continue
            q = min(1.0, max(0.0, (age + 0.02) / 0.12)); sc = 1.0 + 0.35 * (1 - q) ** 2
            fs = int(base * sc); ff = font(fs)
            key = re.sub(r'[^A-Z]', '', words[k])
            col = (255, 196, 84) if key in GOLD_WORDS else (255, 255, 255)
            bw = ff.getbbox(words[k])[2]; px = int(x + widths[k] / 2 - bw / 2); py = int(y - (fs - base) * 0.55)
            ds.text((px + 6, py + 10), words[k], font=ff, fill=int(200 * q))
            dr.text((px, py), words[k], font=ff, fill=col + (int(255 * q),), stroke_width=7, stroke_fill=(0, 0, 0, int(230 * q)))
            x += widths[k] + space
    return np.asarray(im).astype(np.float32) / 255, cv2.GaussianBlur(np.asarray(sh).astype(np.float32) / 255, (0, 0), 14)


SHOTS = None
_cache = OrderedDict()
def scene(name, args):
    key = (name, tuple(args))
    if key in _cache: _cache.move_to_end(key); return _cache[key]
    cls = getattr(S2, name, None) or getattr(S1, name)
    if name == 'City': inst = cls(seed=args[0])
    else: inst = cls(*args)
    _cache[key] = inst
    while len(_cache) > 6: _cache.popitem(last=False)
    return inst


def render_frame(fi):
    global SHOTS
    if SHOTS is None: SHOTS = json.load(open(B + 'shots.json'))
    t = fi / FPS
    idx = max(i for i, s in enumerate(SHOTS) if s['start'] <= t + 1e-6)
    sh = SHOTS[idx]; lt = t - sh['start']; d = sh['end'] - sh['start']
    sc = scene(sh['scene'], sh['args'])
    if sh['scene'] == 'EndCard':
        tags = [w['s'] - END_START for w in WORDS if w['line'] == len(LINES) - 1][2:6]
        img = sc.frame(lt, d, tags)
    elif sh['scene'] == 'Card':
        img = sc.frame(lt, d)
    else:
        t0 = sh.get('t0', 0)
        img = sc.frame(lt + t0, d + t0)
        z = 1.0 + 0.05 * ((lt / d) if sh['zdir'] > 0 else (1 - lt / d))
        img = cam(img, z, W / 2, H / 2)
        if sh['mirror']: img = img[:, ::-1]
    img = grade(img, mix=0.8 if sh['scene'] != 'Trails' else 0.65)
    if idx > 0 and lt < 0.3:
        k = math.exp(-lt * 12)
        img = cam(img, 1.0 + 0.07 * k, W / 2, H / 2)
        img = img + np.asarray((1.0, 0.85, 0.6), np.float32) * (0.55 if sh['scene'] in ('Card', 'EndCard') else 0.3) * math.exp(-lt * 22)
    if sh['end'] - t < 0.07 and idx + 1 < len(SHOTS):
        img = cv2.blur(img, (1, int(1 + 50 * (1 - (sh['end'] - t) / 0.07))))
    img = grain(img, fi, 0.03)
    sub = subtitle_layer(t)
    if sub:
        rgba, shadow = sub
        img = img * (1 - shadow[..., None] * 0.6); a = rgba[..., 3:4]; img = img * (1 - a) + rgba[..., :3] * a
    if t < 0.1: img *= 0.4 + 6 * t
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


def render_seg(k):
    out = f'{B}seg_{k:03d}.mp4'
    if os.path.exists(out): return
    f0 = int(k * SEG * FPS); f1 = min(int((k + 1) * SEG * FPS), int(round(DUR * FPS)))
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-maxrate', '9M', '-bufsize', '18M', '-pix_fmt', 'yuv420p',
                           '-g', '60', out + '.tmp.mp4'], stdin=subprocess.PIPE)
    with Pool(4) as p:
        for fr in p.imap(render_frame, range(f0, f1), chunksize=4): ff.stdin.write(fr.tobytes())
    ff.stdin.close(); ff.wait(); os.rename(out + '.tmp.mp4', out)
    print('segment', k, 'done', flush=True)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'plan':
        sh = plan(); from collections import Counter
        print(len(sh), 'shots'); print(Counter(s['scene'] for s in sh).most_common())
    elif cmd == 'stills':
        ts = [float(x) for x in sys.argv[2].split(',')]
        with Pool(4) as p: frames = p.map(render_frame, [int(x * FPS) for x in ts])
        th = [cv2.resize(f, (270, 480), interpolation=cv2.INTER_AREA) for f in frames]
        while len(th) % 6: th.append(np.zeros_like(th[0]))
        Image.fromarray(np.vstack([np.hstack(th[i:i + 6]) for i in range(0, len(th), 6)])).save(B + 'contact.png')
    elif cmd == 'render':
        nseg = math.ceil(DUR / SEG)
        a = int(sys.argv[2]) if len(sys.argv) > 2 else 0; b = int(sys.argv[3]) if len(sys.argv) > 3 else nseg
        for k in range(a, b): render_seg(k)
    elif cmd == 'concat':
        nseg = math.ceil(DUR / SEG)
        open(B + 'segs.txt', 'w').write(''.join(f"file 'seg_{k:03d}.mp4'\n" for k in range(nseg)))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', B + 'segs.txt', '-c', 'copy', B + 'video_only.mp4'], check=True)
        print('concat ok')
