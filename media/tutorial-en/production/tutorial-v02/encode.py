"""CFR picture revision with the accepted v01 AAC track copied byte-for-byte."""
from pathlib import Path
import json,os,subprocess,hashlib,time,bisect
from PIL import Image,ImageChops,ImageStat
ROOT=Path(__file__).resolve().parents[4];O=ROOT/'media/tutorial-en/out/tutorial-full-v02';V1=ROOT/'media/tutorial-en/out/tutorial-full-v01/SceneFlow-Tutorial-15min-v01-delivery.mp4'
plan=json.loads((O/'frame-hold-plan.json').read_text());cuts=plan['cuts'];total=plan['total'];A=O/'all-frames';A.mkdir(exist_ok=True)
assert(O/'held-complete.json').exists()
for i,start in enumerate(cuts[:-1]):
 src=O/'held-frames'/(str(start).zfill(5)+'.jpg');assert src.exists(),src
 for f in range(start,cuts[i+1]):
  dst=A/(str(f).zfill(5)+'.jpg')
  if not dst.exists():os.link(src,dst)
def run(args):
 p=subprocess.run(args,capture_output=True)
 if p.returncode:raise RuntimeError(p.stderr.decode('utf8',errors='replace')[-1800:])
 return p
target=O/'SceneFlow-Tutorial-15min-v02.mp4'
print('Encoding picture revision; copying the approved voice track unchanged',flush=True)
p=run(['ffmpeg','-hide_banner','-y','-framerate','30','-i',str(A/'%05d.jpg'),'-i',str(V1),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','veryfast','-crf','18','-threads','8','-pix_fmt','yuv420p','-c:a','copy','-frames:v',str(total),'-movflags','+faststart','-progress',str(O/'encode-progress.txt'),str(target)])
(O/'encode.log').write_bytes(p.stderr)
print('Full decoding and audio identity verification',flush=True)
run(['ffmpeg','-v','error','-i',str(target),'-f','null','NUL'])
hashes=[hashlib.sha256(run(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c:a','copy','-f','adts','-']).stdout).hexdigest()for p in [V1,target]]
assert hashes[0]==hashes[1],'Accepted audio changed'
probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(target)]).stdout);v=next(x for x in probe['streams']if x['codec_type']=='video')
assert v['width']==1920 and v['height']==1080 and v['r_frame_rate']=='30/1' and int(v['nb_frames'])==total
assert abs(float(probe['format']['duration'])-901.4)<.1
checks=[]
for q in json.loads((O/'qa-frames.json').read_text()):
 src=O/'held-frames'/(str(plan['frames'][bisect.bisect_right(plan['frames'],q['frame'])-1]).zfill(5)+'.jpg')
 qa=O/f"QA-{q['id']}-{q['t']}.jpg";a=Image.open(qa).convert('RGB');b=Image.open(src).convert('RGB');d=sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3
 checks.append(dict(**q,meanPixelDifference=d));assert d<3,(q['id'],q['t'],d)
(O/'qa-equivalence.json').write_text(json.dumps(checks,indent=2))
(O/'delivery-verified.json').write_text(json.dumps(dict(fullDecode=True,duration=901.4,width=1920,height=1080,fps=30,frames=total,audioUnchanged=True,audioSha256=hashes[0],qaFrames=len(checks),time=time.time()),indent=2))
print('Verified full v02 delivery',flush=True)
