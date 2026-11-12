"""Original deterministic synth score. No downloaded samples or external music."""
from pathlib import Path
import json, wave
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SR = 48000
SECONDS = 20
BPM = 120
rng = np.random.default_rng(2312)
mix = np.zeros((SR * SECONDS, 2), dtype=np.float64)

def add(at, signal, gain=1.0, pan=0.0):
    start = round(at * SR)
    end = min(len(mix), start + len(signal))
    if end <= start:
        return
    x = signal[:end-start] * gain
    mix[start:end, 0] += x * np.sqrt((1-pan)/2)
    mix[start:end, 1] += x * np.sqrt((1+pan)/2)

def time(duration):
    return np.arange(round(duration * SR)) / SR

def freq(midi):
    return 440 * 2 ** ((midi - 69) / 12)

def kick(at, gain=1):
    t = time(.42)
    phase = 2*np.pi*(47*t + 100*.025*(1-np.exp(-t/.025)))
    signal = np.sin(phase)*np.exp(-t*12) + rng.normal(0, .11, len(t))*np.exp(-t*160)
    add(at, signal, .72*gain)

def snare(at, gain=1):
    t = time(.24)
    noise = rng.normal(0, 1, len(t))
    noise = noise - np.roll(noise, 1)
    signal = noise*.19*np.exp(-t*24) + .16*np.sin(2*np.pi*180*t)*np.exp(-t*35)
    add(at, signal, gain)

def hat(at, gain=.1, opened=False):
    t = time(.17 if opened else .06)
    n = rng.normal(0, 1, len(t))
    add(at, (n-np.roll(n,1))*np.exp(-t*(25 if opened else 95)), gain, .28)

# C minor / Ab / Eb / Bb, with a final dominant and resolution.
roots = [36, 32, 39, 34, 36, 32, 39, 34, 31, 36]
triads = [[60,63,67],[56,60,63],[58,63,67],[58,62,65],
          [60,63,67],[56,60,63],[58,63,67],[58,62,65],[59,62,67],[60,63,67]]
for bar in range(10):
    at = bar*2
    t = time(2.7)
    envelope = np.minimum(t/.13, 1)*np.minimum((2.7-t)/.65, 1)
    chord = sum(np.sin(2*np.pi*freq(note)*t + .16*np.sin(2*np.pi*.35*t))
                + .2*np.sin(2*np.pi*freq(note)*2.002*t) for note in triads[bar])/3
    add(at, chord*envelope, .13, -.18)
    for step in range(8):
        when = at + step*.25
        t = time(.42)
        note = triads[bar][[0,2,1,2,0,1,2,1][step]] + (12 if step in (3,7) else 0)
        hz = freq(note)
        arp = (np.sin(2*np.pi*hz*t) + .22*np.sin(2*np.pi*hz*2*t)
               + .08*np.sin(2*np.pi*hz*3*t)) * (1-np.exp(-t*250))*np.exp(-t*11)
        strength = .13 if when < 2 else .21
        add(when, arp, strength, -.5 if step%2 else .5)
        add(when+.375, arp, strength*.25, .5 if step%2 else -.5)
    for beat in range(4):
        when = at+beat*.5
        t = time(.33)
        bass = (np.sin(2*np.pi*freq(roots[bar])*t) + .17*np.sin(2*np.pi*freq(roots[bar])*2*t))
        bass *= (1-np.exp(-t*100))*np.exp(-t*8)
        add(when+.04, bass, .31)
        if when >= 2 and when < 19:
            kick(when, .9 if beat in (0,2) else .52)
            if beat%2:
                snare(when, .85)
            hat(when+.25, .052, beat==3)
            hat(when, .025)
        elif beat == 0:
            kick(when, .65)

for at in [4, 8, 11, 15, 19]:
    start = max(0, at-.3)
    t = time(.3)
    n = rng.normal(0,1,len(t))
    n = np.convolve(n,np.ones(12)/12,mode='same')
    add(start,n*(t/.3)**2,.13,-.3)
    t = time(.45)
    add(at,rng.normal(0,1,len(t))*np.exp(-t*13),.045,.35)

# Final clean logo impact and controlled release.
kick(19, 1.15)
t = np.arange(len(mix))/SR
mix *= np.minimum(t/.018,1)[:,None]
mix *= np.clip((20-t)/.55,0,1)[:,None]
mix = np.tanh(mix*1.15)
mix *= .88 / max(np.max(np.abs(mix)), 1e-8)
output = ROOT/'public/audio/sceneflow-pulse-120.wav'
output.parent.mkdir(parents=True,exist_ok=True)
with wave.open(str(output),'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((mix*32767).astype('<i2').tobytes())
receipt = {'bpm':BPM,'seconds':SECONDS,'sampleRate':SR,'channels':2,
           'peakDbFS':float(20*np.log10(np.max(np.abs(mix)))),
           'rmsDbFS':float(20*np.log10(np.sqrt(np.mean(mix**2)))),
           'origin':'Original procedural synthesizer score; no third-party samples.',
           'frameRate':30,'framesPerBeat':15,'majorCutFrames':[0,120,240,330,450,570],
           'notice':'RMS is not an integrated LUFS measurement.'}
(ROOT/'out/promo-sample-v01').mkdir(parents=True,exist_ok=True)
(ROOT/'out/promo-sample-v01/score.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
