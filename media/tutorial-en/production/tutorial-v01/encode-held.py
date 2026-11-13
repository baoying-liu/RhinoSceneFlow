"""Lossless frame holds + unchanged PCM phrases, encoded at a constant 30 fps."""
from pathlib import Path
import json,os,wave,subprocess,time
ROOT=Path(__file__).resolve().parents[4];O=ROOT/'media/tutorial-en/out/tutorial-full-v01';F=O/'held-frames';A=O/'all-frames';A.mkdir(exist_ok=True)
assert (O/'held-complete.json').exists()
plan=json.loads((O/'frame-hold-plan.json').read_text());cuts=plan['cuts'];total=plan['total'];print('Preparing constant-rate frame sequence',flush=True)
for i,start in enumerate(cuts[:-1]):
 source=F/(str(start).zfill(5)+'.jpg');assert source.exists(),source
 for f in range(start,cuts[i+1]):
  target=A/(str(f).zfill(5)+'.jpg')
  if not target.exists():os.link(source,target)
rows=json.loads((O/'timeline.json').read_text());sr=24000;pcm=bytearray(round(total/30*sr)*2)
for c in rows:
 with wave.open(str(ROOT/'artifacts/tutorial-full-v01/local-voice'/(c['id']+'.wav'))) as w:
  assert w.getframerate()==sr and w.getnchannels()==1 and w.getsampwidth()==2
  raw=w.readframes(w.getnframes())
 begin=round((c['start']/30+.7)*sr)*2;pcm[begin:begin+len(raw)]=raw
audio=O/'Narration-Master.wav'
with wave.open(str(audio),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm)
print('Encoding 30 fps with the original phrase timings',flush=True)
args=['ffmpeg','-hide_banner','-y','-framerate','30','-i',str(A/'%05d.jpg'),'-i',str(audio),'-c:v','libx264','-preset','veryfast','-crf','18','-threads','8','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-frames:v',str(total),'-movflags','+faststart','-progress',str(O/'encode-progress.txt'),str(O/'SceneFlow-Tutorial-15min-v01.mp4')]
p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf8',errors='replace')
(O/'held-encode.log').write_text(p.stderr,encoding='utf8')
if p.returncode:raise RuntimeError(p.stderr[-1600:])
print('Constant-rate tutorial encoded',flush=True)
