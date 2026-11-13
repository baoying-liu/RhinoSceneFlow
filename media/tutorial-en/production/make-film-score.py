"""Original 120-second score: all synthesized, no external samples/services."""
from pathlib import Path
import numpy as np,wave,json
V=Path(__file__).resolve().parents[1];SR=48000;DURATION=120;BPM=120
rng=np.random.default_rng(233);mix=np.zeros((SR*DURATION,2),np.float32)
def t(d):return np.arange(round(d*SR),dtype=np.float64)/SR
def hz(n):return 440*2**((n-69)/12)
def add(at,x,gain=1,pan=0):
 start=round(at*SR);end=min(len(mix),start+len(x))
 if start<0 or end<=start:return
 x=x[:end-start]*gain;mix[start:end,0]+=x*np.sqrt((1-pan)/2);mix[start:end,1]+=x*np.sqrt((1+pan)/2)
def kick(at,g=1):
 a=t(.5);p=2*np.pi*(43*a+130*.025*(1-np.exp(-a/.025)));add(at,(np.sin(p)*np.exp(-a*12)+rng.normal(0,.09,len(a))*np.exp(-a*190)),.65*g)
def hat(at,g=.03):
 a=t(.09);n=rng.normal(0,1,len(a));add(at,(n-np.roll(n,1))*np.exp(-a*65),g,.35)
def snare(at,g=.5):
 a=t(.24);n=rng.normal(0,1,len(a));add(at,(n-np.roll(n,1))*.17*np.exp(-a*23)+.12*np.sin(2*np.pi*180*a)*np.exp(-a*35),g,-.12)
roots=[38,34,41,36];triads=[[62,65,69],[58,62,65],[60,65,69],[60,64,67]]
for bar in range(60):
 at=bar*2;ix=bar%4;tri=triads[ix];a=t(2.8);env=np.minimum(a/.3,1)*np.minimum((2.8-a)/.6,1)
 pad=sum(np.sin(2*np.pi*hz(n)*a+.22*np.sin(2*np.pi*.24*a))+.12*np.sin(2*np.pi*hz(n)*2.001*a) for n in tri)/3
 add(at,pad*env,.15,-.3)
 full=18<=at<60 or 82<=at<118;light=6<=at<18 or 60<=at<82
 for step in range(8):
  when=at+step*.25;a=t(.6);n=tri[[0,2,1,2,0,1,2,1][step]]+(12 if step in (3,7) else 0)
  signal=(np.sin(2*np.pi*hz(n)*a)+.19*np.sin(2*np.pi*hz(n)*2*a))*(1-np.exp(-a*130))*np.exp(-a*9)
  gain=.16 if full else .11 if light else .07;add(when,signal,gain,(-.55 if step%2 else .55));add(when+.375,signal,gain*.24,(.55 if step%2 else -.55))
 for beat in range(4):
  when=at+beat*.5;a=t(.4);bass=(np.sin(2*np.pi*hz(roots[ix])*a)+.12*np.sin(2*np.pi*hz(roots[ix])*2*a))*(1-np.exp(-a*100))*np.exp(-a*7)
  add(when+.025,bass,.31 if full else .18)
  if full:
   kick(when,.95 if beat in (0,2) else .55)
   if beat%2:snare(when,.85)
   hat(when+.25,.04);hat(when,.025)
  elif light and beat in (0,2):kick(when,.6);hat(when+.25,.02)
  elif beat==0:kick(when,.45)
for at in [6,18,30,40,48,60,68,82,92,102,112,117]:
 a=t(.45);n=rng.normal(0,1,len(a));n=np.convolve(n,np.ones(16)/16,mode='same');add(at-.45,n*(a/.45)**2,.19,-.25)
 a=t(.8);add(at,np.sin(2*np.pi*hz(38)*a)*np.exp(-a*7),.38);add(at,rng.normal(0,1,len(a))*np.exp(-a*12),.04,.25)
# A resolved D-minor ending after the final visual montage.
a=t(3);env=np.minimum(a/.03,1)*np.exp(-a*1.6);add(117,sum(np.sin(2*np.pi*hz(n)*a) for n in [50,62,65,69])/4*env,.32)
clock=np.arange(len(mix))/SR;mix*=np.minimum(clock/.025,1)[:,None];mix*=np.clip((DURATION-clock)/1.6,0,1)[:,None];mix=np.tanh(mix*1.1);mix*=.88/max(float(np.abs(mix).max()),1e-9)
p=V/'public/audio/sceneflow-film-120.wav';p.parent.mkdir(parents=True,exist_ok=True)
with wave.open(str(p),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((mix*32767).astype('<i2').tobytes())
out=V/'out/promo-film-v02';out.mkdir(parents=True,exist_ok=True);(out/'score.json').write_text(json.dumps(dict(seconds=DURATION,bpm=BPM,framesPerBeat=15,sampleRate=SR,peakDbFS=float(20*np.log10(np.abs(mix).max())),rmsDbFS=float(20*np.log10(np.sqrt(np.mean(mix**2)))),origin='Original deterministic synth composition; no third-party samples or AI voice'),indent=2));print('Original two-minute score saved')
