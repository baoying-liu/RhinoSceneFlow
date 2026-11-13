"""Original section-scored music: sparse interaction, peaks, breathing room."""
from pathlib import Path
import numpy as np,wave,json
V=Path(__file__).resolve().parents[1];sr=48000;seconds=252;rng=np.random.default_rng(606);mix=np.zeros((sr*seconds,2),np.float32)
def time(d):return np.arange(round(d*sr))/sr
def hz(n):return 440*2**((n-69)/12)
def add(at,x,g=1,pan=0):
 a=round(at*sr);b=min(len(mix),a+len(x))
 if a<0 or b<=a:return
 v=x[:b-a]*g;mix[a:b,0]+=v*np.sqrt((1-pan)/2);mix[a:b,1]+=v*np.sqrt((1+pan)/2)
def piano(at,n,d=1.6,g=.14,pan=0):
 t=time(d);s=sum(np.sin(2*np.pi*hz(n)*k*(1+.00018*k*k)*t)*np.exp(-t*(1.3+k*.8))/k**1.5 for k in range(1,6));env=(1-np.exp(-t*160))*np.minimum((d-t)/.13,1);add(at,s*env,g,pan)
def pad(at,notes,d,g=.1):
 t=time(d);env=np.minimum(t/.65,1)*np.minimum((d-t)/1.2,1);s=sum(np.sin(2*np.pi*hz(n)*t+.03*np.sin(2*np.pi*4.7*t))+.18*np.sin(2*np.pi*hz(n)*2.002*t) for n in notes)/len(notes);add(at,s*env,g,-.2)
def kick(at,g=.45):
 t=time(.6);phase=2*np.pi*(40*t+95*.03*(1-np.exp(-t/.03)));add(at,np.sin(phase)*np.exp(-t*12),g)
def clap(at,g=.07):
 t=time(.22);n=rng.normal(size=len(t));add(at,(n-np.roll(n,1))*np.exp(-t*30),g,.2)
def tick(at,g=.016):
 t=time(.09);n=rng.normal(size=len(t));add(at,(n-np.roll(n,1))*np.exp(-t*65),g,-.3)
# Section boundaries follow the actual sample timeline, not one repeated arrangement.
sections=[(0,8,'anticipation',.45),(8,24,'interaction',.52),(24,32,'precision',.58),(32,42,'pulse',.95),(42,58,'organic',.57),(58,68,'precision',.62),(68,82,'build',.84),(82,94,'refine',.55),(94,106,'flight',.78),(106,118,'build',.92),(118,128,'pulse',1.03),(128,138,'flight',.65),(138,150,'precision',.54),(150,170,'layers',.43),(170,186,'intent',.5),(186,194,'reveal',1.0),(194,206,'observe',.42),(206,208,'resolve',.45),(208,226,'refine',.55),(226,238,'finale',1.1),(238,248,'build',.78),(248,252,'resolve',.5)]
chords=[[50,57,60,64],[46,53,57,62],[48,55,60,64],[48,55,59,62]]
for a,b,kind,energy in sections:
 for at in np.arange(a,b,2):
  ix=int(at//2)%4;ch=chords[ix];pad(float(at),ch,3.8,.16*energy)
  piano(float(at)+.03,ch[0],2,.20*energy)
  if kind in ['interaction','organic','precision','intent','refine']:
   for j,n in enumerate([ch[1]+12,ch[2]+12,ch[3]+12]):piano(float(at)+[.15,.85,1.5][j],n,1.5,.12*energy,[-.35,.3,0][j])
   if kind in ['organic','precision']:
    kick(float(at),.21);tick(float(at)+1.5,.014)
  elif kind in ['pulse','build','reveal','finale']:
   for beat in range(4):
    when=float(at)+beat*.5;kick(when,.46*energy if beat%2==0 else .25*energy);piano(when+.06,ch[0]+12,.45,.13*energy)
    if beat%2:clap(when,.055*energy)
    tick(when+.25,.018*energy)
   melody=[69,72,74,77,76,74,72,69]
   for j in range(4):piano(float(at)+j*.5,melody[(int(at*2)+j)%8],1.1,.12*energy,(-.4 if j%2 else .4))
   if kind=='finale':pad(float(at),[n+12 for n in ch],3.9,.15)
  elif kind=='flight':
   piano(float(at)+.2,ch[2]+12,2.8,.15,-.3);piano(float(at)+1.2,ch[3]+12,2.4,.12,.4)
  elif kind=='layers':
   piano(float(at)+.1,ch[1]+12,2.8,.12,.3);kick(float(at),.13)
  elif kind in ['observe','anticipation']:
   piano(float(at)+.4,ch[2]+12,2.8,.09,-.2)
  elif kind=='resolve':piano(float(at)+.05,74,3,.16);piano(float(at)+.35,69,2.6,.1,.35)
# Short arranged breaks before the layer section and final output reveal.
clock=np.arange(len(mix))/sr
for at in [32,68,94,118,150,186,208,226]:
 before=(clock>=at-.22)&(clock<at);mix[before]*=np.linspace(1,.08,before.sum())[:,None]
 t=time(.8);low=rng.normal(size=len(t));low=np.convolve(low,np.ones(32)/32,mode='same');add(at-.8,low*np.linspace(0,1,len(t))**3,.13,-.25)
 kick(at,.30 if at in [186,226] else .17)
# Decisive completion accents without an effect on every cut.
for at,n in [(19.2,81),(53.5,79),(149,76),(225.5,77)]:piano(at,n,.9,.12,.2)
mix*=np.minimum(clock/.18,1)[:,None];mix*=np.clip((seconds-clock)/1.6,0,1)[:,None];mix=np.tanh(mix*1.1);mix*=.86/max(abs(mix).max(),1e-9)
p=V/'public/audio/sceneflow-full-v06.wav'
with wave.open(str(p),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((mix*32767).astype('<i2').tobytes())
metrics=[dict(start=a,end=b,section=k,rmsDb=float(20*np.log10(max(1e-9,np.sqrt(np.mean(mix[int(a*sr):int(b*sr)]**2)))))) for a,b,k,_ in sections]
o=V/'out/promo-final-v06';o.mkdir(parents=True,exist_ok=True);(o/'music-sections.json').write_text(json.dumps(metrics,indent=2));print('Original section-scored music completed; section RMS range',min(x['rmsDb'] for x in metrics),max(x['rmsDb'] for x in metrics))

