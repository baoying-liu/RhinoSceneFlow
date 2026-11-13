"""Local-only Qwen 1.7B voice trial; no cloud credentials or voice uploads."""
import os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
import json
import time
from pathlib import Path
import numpy as np
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

folder = Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/production/voice-private'
model_path = Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/qwen-models/Qwen3-TTS-12Hz-1.7B-Base'
output = folder/'Local-Qwen-1.7B-English-Trial-v2.wav'
text = 'Welcome to SceneFlow. Today we will create materials, place plants, and export a layered image from Rhino.'
transcript = json.loads((folder/'reference-transcript-small.json').read_text(encoding='utf8'))
reference_text = ' '.join(s['text'].strip() for s in transcript['segments'])
torch.set_num_threads(6)
torch.manual_seed(42)
start=time.perf_counter()
print('Loading local model with bfloat16 / SDPA.',flush=True)
model=Qwen3TTSModel.from_pretrained(str(model_path),device_map='cuda:0',dtype=torch.bfloat16,
    attn_implementation='sdpa',local_files_only=True)
loaded=time.perf_counter()
torch.cuda.reset_peak_memory_stats()
print('Building reference prompt from local recording.',flush=True)
prompt=model.create_voice_clone_prompt(ref_audio=str(folder/'baoying-reference-24k-mono.wav'),
    ref_text=reference_text,x_vector_only_mode=False)
print('Synthesizing English trial on GPU.',flush=True)
generated=time.perf_counter()
wavs,sr=model.generate_voice_clone(text=text,language='English',voice_clone_prompt=prompt,
    max_new_tokens=256)
audio=np.asarray(wavs[0],dtype=np.float32)
sf.write(output,audio,sr,subtype='PCM_16')
duration=len(audio)/sr
receipt={'model':'Qwen/Qwen3-TTS-12Hz-1.7B-Base','sample_rate':sr,'duration_seconds':duration,
    'load_seconds':loaded-start,'synthesis_seconds':time.perf_counter()-generated,
    'total_seconds':time.perf_counter()-start,'peak_allocated_gib':torch.cuda.max_memory_allocated()/1024**3,
    'peak_reserved_gib':torch.cuda.max_memory_reserved()/1024**3,'text':text,
    'peak_amplitude':float(np.max(np.abs(audio))),'finite':bool(np.isfinite(audio).all()),
    'cloud_calls':0,'seed':42,'attention':'sdpa','reference_transcript_source':'local small.en ASR'}
(folder/'local-trial-receipt-v2.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps(receipt),flush=True)
