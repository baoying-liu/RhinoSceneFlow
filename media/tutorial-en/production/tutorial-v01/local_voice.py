"""Local reference clone, complete semantic cues, unchanged pitch and rate."""
import os
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
from pathlib import Path
import json,sys,time
import numpy as np,soundfile as sf,torch
from qwen_tts import Qwen3TTSModel
ROOT=Path(__file__).resolve().parents[4];F=ROOT/'artifacts/tutorial-full-v01/local-voice';F.mkdir(parents=True,exist_ok=True)
private=Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/production/voice-private'
data=json.loads(Path(__file__).with_name('script.json').read_text(encoding='utf8'));cues=data['cues']
if len(sys.argv)>1 and sys.argv[1]!='all':cues=[c for c in cues if c['id'] in sys.argv[1:]]
torch.set_num_threads(6);torch.manual_seed(43)
model=Qwen3TTSModel.from_pretrained(str(Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/qwen-models/Qwen3-TTS-12Hz-1.7B-Base'),device_map='cuda:0',dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True)
transcript=json.loads((private/'reference-transcript-small.json').read_text(encoding='utf8'))
prompt=model.create_voice_clone_prompt(ref_audio=str(private/'baoying-reference-24k-mono.wav'),ref_text=' '.join(s['text'].strip() for s in transcript['segments']),x_vector_only_mode=False)
print('Local voice loaded',flush=True)
for cue in cues:
 target=F/(cue['id']+'.wav')
 if target.exists():continue
 start=time.monotonic();torch.manual_seed(43)
 waves,sr=model.generate_voice_clone(text=cue['en'],language='English',voice_clone_prompt=prompt,max_new_tokens=900)
 a=np.asarray(waves[0],dtype=np.float32);sf.write(target,a,sr,subtype='PCM_16')
 r=dict(id=cue['id'],duration=len(a)/sr,seconds=time.monotonic()-start,cloudCalls=0,model='Qwen3-TTS-12Hz-1.7B-Base',auditoryReview='unverified',pitchRate='unchanged')
 target.with_suffix('.receipt.json').write_text(json.dumps(r),encoding='utf8');print(json.dumps(r),flush=True)
