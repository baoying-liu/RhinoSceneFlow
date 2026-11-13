"""Original deterministic wind-like transition sound, no external samples."""
from pathlib import Path
import numpy as np
import wave
sr=48000
n=int(.8*sr)
t=np.arange(n)/sr
x=np.random.default_rng(41).normal(size=n)
x=(x-np.convolve(x,np.ones(15)/15,mode="same"))*np.sin(np.pi*t/.8)**3
x=x/max(abs(x))*.28
st=np.column_stack([x,np.roll(x,120)])
p=Path(__file__).resolve().parents[1]/"public/audio/sceneflow-whoosh.wav"
with wave.open(str(p),"wb") as w:
 w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((st*32767).astype("<i2").tobytes())
