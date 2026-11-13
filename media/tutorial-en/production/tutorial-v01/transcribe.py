from pathlib import Path
import json,sys
from faster_whisper import WhisperModel
ROOT=Path(__file__).resolve().parents[4];F=ROOT/'artifacts/tutorial-full-v01/voice'
model=WhisperModel('small.en',device='cpu',compute_type='int8',local_files_only=True,cpu_threads=6)
for f in sorted(F.glob('*.wav')):
 out=f.with_suffix('.asr.json')
 if out.exists():continue
 segs,info=model.transcribe(str(f),language='en',word_timestamps=True,beam_size=3,vad_filter=True)
 data=[dict(start=s.start,end=s.end,text=s.text,words=[dict(start=w.start,end=w.end,word=w.word,probability=w.probability) for w in s.words]) for s in segs]
 out.write_text(json.dumps(data,indent=2),encoding='utf8');print(f.stem,[(round(s['start'],1),round(s['end'],1),s['text']) for s in data],flush=True)
