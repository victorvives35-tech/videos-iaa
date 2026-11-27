import json,sys,numpy as np,soundfile as sf
from kokoro_onnx import Kokoro
K=sys.argv[1]
k=Kokoro(K+'/model.onnx',K+'/voices.bin')
lines=json.load(open('script.json'))
for i,t in enumerate(lines):
    a,sr=k.create(t,voice='am_onyx',lang='en-us',speed=1.0 if i<12 else 0.9)
    sf.write(f'build/vo_{i:02d}.wav',a,sr); print(i,round(len(a)/sr,2),t)
