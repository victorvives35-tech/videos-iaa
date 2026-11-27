# Procedural cinematic score: D minor, i-VI-III-VII, building intensity, impacts on key moments.
import numpy as np, soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt
SR = 48000; DUR = 35.5; N = int(SR*DUR); rng = np.random.default_rng(7)
t = np.arange(N)/SR
L = np.zeros(N); R = np.zeros(N)
def hz(n): return 440*2**((n-69)/12)
def add(sig, start, pan=0.0, gain=1.0):
    k = int(start*SR); sig = sig[:max(0, N-k)]
    if k < 0: sig = sig[-k:]; k = 0
    L[k:k+len(sig)] += sig*gain*np.sqrt(0.5*(1-pan)); R[k:k+len(sig)] += sig*gain*np.sqrt(0.5*(1+pan))
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def env_adsr(n, a, r):
    e = np.ones(n); na, nr = int(a*SR), int(r*SR)
    e[:na] = np.linspace(0,1,na)**2; e[-nr:] *= np.linspace(1,0,nr)**2; return e
def saw(f, n, det=0.0):
    tt = np.arange(n)/SR; ph = rng.random()
    return 2*((f*(1+det)*tt+ph) % 1)-1

# intensity curve over time (0..1)
def intensity(x): return np.interp(x, [0,4,8,13,19,21.4,28.6,30,35.5],[0.35,0.45,0.55,0.65,0.8,1.0,1.0,0.6,0.0])

# --- chord pad (strings) ---
prog = [[50,57,62,65],[46,53,58,62],[53,57,60,65],[48,55,60,64]]  # Dm Bb F C
CH = 4.8
for ci in range(8):
    st = ci*CH - 0.3
    if st > 29: break
    notes = prog[ci % 4]; n = int((CH+1.2)*SR)
    s = np.zeros(n)
    for nt in notes:
        for d in (-0.004, 0, 0.0045): s += saw(hz(nt), n, d)
        s += 0.5*saw(hz(nt+12), n, 0.002)
    tt = np.arange(n)/SR
    cutoff = 900 + 2600*intensity(st+2)
    s = lp(s, cutoff, 2) * (1+0.15*np.sin(2*np.pi*5*tt))  # light tremolo/vibrato feel
    add(s*env_adsr(n, 0.9, 1.2)*0.022, st, pan=0.0)
# end-card chord: big Dm with high octave
n = int(6.8*SR); s = np.zeros(n)
for nt in [38,50,57,62,65,69,74]:
    for d in (-0.003,0,0.003): s += saw(hz(nt), n, d)
s = lp(s, 2200, 2); add(s*env_adsr(n, 0.05, 5.0)*0.02, 28.7)

# --- sub drone ---
drone = np.sin(2*np.pi*hz(26)*t) + 0.5*np.sin(2*np.pi*hz(38)*t)
drone *= np.clip(intensity(t)*1.2, 0, 1) * np.clip((28.6-t)/0.4, 0, 1)
add(drone*0.10, 0)

# --- impacts ---
def boom(size=1.0, length=3.5):
    n = int(length*SR); tt = np.arange(n)/SR
    f = 30 + 70*np.exp(-tt*12)
    body = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-tt*(1.6/size))
    noise = lp(rng.standard_normal(n), 3000) * np.exp(-tt*9)
    crack = hp(rng.standard_normal(n), 2000) * np.exp(-tt*35)
    return np.tanh(1.6*body) + 0.35*noise + 0.15*crack
for when, g in [(0.0,1.0),(8.5,0.55),(13.5,0.6),(16.3,0.65),(21.42,1.0),(24.9,0.6),(28.68,1.2)]:
    add(boom(1.0 if g<1 else 1.6), when, gain=0.55*g)

# --- whoosh / risers ---
def riser(length):
    n = int(length*SR); x = rng.standard_normal(n); tt = np.arange(n)/SR
    out = np.zeros(n); seg = 2048
    for i in range(0, n, seg):
        fc = 300 + 7000*(i/n)**2
        out[i:i+seg] = lp(x[i:i+seg], fc, 1)
    return out * (tt/length)**2
add(riser(2.2), 19.2, gain=0.35); add(riser(1.2), 27.48, gain=0.4)
def whoosh(length=0.6):
    n=int(length*SR); tt=np.arange(n)/SR; x=lp(hp(rng.standard_normal(n),400),3500)
    return x*np.sin(np.pi*tt/length)**3
cuts = [2.3,4.5,6.1,8.5,11.1,13.5,16.3,19.1,20.0,20.6,21.4,24.9,26.8]
for c in cuts: add(whoosh(), c-0.32, pan=rng.uniform(-.5,.5), gain=0.09)

# --- heartbeat (0-4.4) ---
def kick(g=1.0):
    n=int(0.5*SR); tt=np.arange(n)/SR
    return np.sin(2*np.pi*np.cumsum(45+120*np.exp(-tt*30))/SR)*np.exp(-tt*9)*g
for b in np.arange(0.9, 4.4, 0.75): add(kick(0.5), b); add(kick(0.3), b+0.22)

# --- string ostinato (16ths) from 4.5s, D pedal with chord tones ---
BPM = 100; s16 = 60/BPM/4
x = 4.5; k = 0
while x < 28.6:
    ci = int((x+0.3)//CH) % 4; root = prog[ci][0]
    pat = [0,0,12,0,7,0,12,7]
    nt = root-12+pat[k % 8]
    n = int(0.22*SR); tt = np.arange(n)/SR
    s = (saw(hz(nt), n) + saw(hz(nt), n, 0.003)) * np.exp(-tt*14)
    s = lp(s, 1200+2500*intensity(x))
    add(s*0.06*(0.5+0.7*intensity(x)), x, pan=0.25*np.sin(k))
    x += s16; k += 1

# --- toms/epic drums from 13.5, full from 21.4 ---
def tom(f=90, g=1.0):
    n=int(0.6*SR); tt=np.arange(n)/SR
    b=np.sin(2*np.pi*np.cumsum(f*(1+0.6*np.exp(-tt*25)))/SR)*np.exp(-tt*7)
    return (b + 0.3*lp(rng.standard_normal(n),1500)*np.exp(-tt*20))*g
beat = 60/BPM
x = 13.5; i = 0
while x < 28.6:
    full = x >= 21.4
    if i % 4 == 0: add(tom(70, 0.6 if not full else 0.9), x)
    if full or i % 2 == 0: add(tom(110, 0.25 if not full else 0.45), x+beat/2, pan=-0.3)
    if full and i % 4 == 2: add(tom(140,0.4), x, pan=0.3); add(hp(rng.standard_normal(int(.3*SR)),1500)*np.exp(-np.arange(int(.3*SR))/SR*12)*0.25, x)
    x += beat; i += 1
# build roll 19.2-21.4
x=19.2
while x < 21.4:
    add(tom(120, 0.15+0.35*(x-19.2)/2.2), x, pan=rng.uniform(-.4,.4)); x += max(0.06, 0.2-(x-19.2)*0.07)

# high choir-ish pad on climax
n=int(7.2*SR); tt=np.arange(n)/SR; s=np.zeros(n)
for nt in [74,77,81]:
    s += np.sin(2*np.pi*hz(nt)*tt*(1+0.003*np.sin(2*np.pi*5.5*tt))) + 0.3*np.sin(2*np.pi*2*hz(nt)*tt)
add(s*env_adsr(n,1.0,1.5)*0.025, 21.4)

# --- reverb ---
irn = int(2.8*SR); it = np.arange(irn)/SR
irL = rng.standard_normal(irn)*np.exp(-it*2.4); irR = rng.standard_normal(irn)*np.exp(-it*2.4)
irL, irR = lp(irL, 5000)/30, lp(irR, 5000)/30
wetL = fftconvolve(L, irL)[:N]; wetR = fftconvolve(R, irR)[:N]
L2 = L*0.8 + wetL*0.6; R2 = R*0.8 + wetR*0.6
# master fade
fade = np.clip((DUR-t)/1.5, 0, 1); L2*=fade; R2*=fade
m = np.stack([L2, R2], 1); m /= np.abs(m).max()*1.05
m = np.tanh(m*1.4)/np.tanh(1.4)
sf.write('build/music.wav', m.astype(np.float32), SR)
print('music ok', m.shape)
