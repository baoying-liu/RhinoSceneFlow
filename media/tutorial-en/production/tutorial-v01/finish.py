"""Loudness-only delivery master, complete decode and stream verification."""
from pathlib import Path
import subprocess,json,re,time
ROOT=Path(__file__).resolve().parents[4];O=ROOT/'media/tutorial-en/out/tutorial-full-v01'
raw=O/'SceneFlow-Tutorial-15min-v01.mp4';target=O/'SceneFlow-Tutorial-15min-v01-delivery.mp4'
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,encoding='utf8',errors='replace')
 if p.returncode:raise RuntimeError(p.stderr[-1800:])
 return p
print('Measuring narration loudness',flush=True)
p=run(['ffmpeg','-hide_banner','-i',str(raw),'-vn','-af','loudnorm=I=-18:TP=-1.5:LRA=11:print_format=json','-f','null','NUL'])
stats=json.loads(re.findall(r'\{\s*"input_i".*?\}',p.stderr,re.S)[-1]);(O/'audio-loudness-measured.json').write_text(json.dumps(stats,indent=2))
af='loudnorm=I=-18:TP=-1.5:LRA=11:measured_I='+stats['input_i']+':measured_TP='+stats['input_tp']+':measured_LRA='+stats['input_lra']+':measured_thresh='+stats['input_thresh']+':offset='+stats['target_offset']+':linear=true:print_format=json'
print('Writing delivery audio; copying video pixels unchanged',flush=True)
p=run(['ffmpeg','-hide_banner','-y','-i',str(raw),'-map','0:v:0','-map','0:a:0','-c:v','copy','-af',af,'-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(target)])
(O/'audio-loudness-delivery.log').write_text(p.stderr,encoding='utf8')
print('Decoding the entire delivery',flush=True)
run(['ffmpeg','-v','error','-i',str(target),'-f','null','NUL'])
probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(target)]).stdout)
v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'])==(1920,1080) and v['r_frame_rate']=='30/1'
assert a['codec_name']=='aac' and a['sample_rate']=='48000'
assert 900<float(probe['format']['duration'])<910
(O/'delivery-probe.json').write_text(json.dumps(probe,indent=2),encoding='utf8')
(O/'delivery-verified.json').write_text(json.dumps(dict(fullDecode=True,duration=float(probe['format']['duration']),width=v['width'],height=v['height'],fps=30,audio=a['codec_name'],auditoryReview='unverified',time=time.time()),indent=2),encoding='utf8')
print('Delivery verified: '+str(target),flush=True)
