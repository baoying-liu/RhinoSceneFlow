"""Bounded reference-conditioned narration. Raw responses stay private."""
from pathlib import Path
import sys,os,json,base64,urllib.request,urllib.error,urllib.parse,time,concurrent.futures
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qwen_credentials import load_credentials
OUT=ROOT/'artifacts/tutorial-full-v01/voice';OUT.mkdir(parents=True,exist_ok=True)
PRIVATE=Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/production/voice-private/tutorial-full-v01';PRIVATE.mkdir(parents=True,exist_ok=True)
def run(cue):
 target=OUT/(cue['id']+'.wav');receipt=OUT/(cue['id']+'.receipt.json')
 if target.exists():return dict(id=cue['id'],reused=True)
 raw=PRIVATE/(cue['id']+'.response.json')
 if raw.exists():d=json.loads(raw.read_text())
 else:
  cred=load_credentials();ref=PRIVATE.parent/'baoying-reference-24k-mono.wav'
  prompt=('Single English speaker, match reference @voice1. An engaging hands-on software teacher: '
   'warm, energetic, confident and enthusiastic, with a friendly smile and expressive natural emphasis. '
   'Clear complete consonants, smooth connected phrasing, conversational moderate pace, not flat, not slow or robotic. '
   'No music, no sound effects, no invented words. Speak the following quoted passage exactly once and stop. '
   '@voice1 says: "'+cue['en']+'"')
  payload=dict(model='qwen-audio-3.1-tts-next',input=dict(text_prompt=prompt,references=[dict(audio_data='data:audio/wav;base64,'+base64.b64encode(ref.read_bytes()).decode())],format='wav',sample_rate=24000,channels=1,seed=43))
  req=urllib.request.Request(cred['base_url']+'/api/v1/services/audio/tts/SpeechSynthesizer',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+cred['api_key'],'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(req,timeout=180) as response:d=json.load(response)
  except urllib.error.HTTPError as e:
   error=json.loads(e.read());return dict(id=cue['id'],failed=True,http=e.code,code=error.get('code'))
  raw.write_text(json.dumps(d),encoding='utf8')
 a=d['output']['audio']
 if a.get('data'):content=base64.b64decode(a['data'])
 else:
  u=urllib.parse.urlsplit(a['url']);assert u.hostname=='dashscope-result-sgp.oss-ap-southeast-1.aliyuncs.com'
  with urllib.request.urlopen(urllib.parse.urlunsplit(u._replace(scheme='https')),timeout=60) as response:content=response.read()
 target.write_bytes(content)
 result=dict(id=cue['id'],bytes=len(content),usage=d.get('usage'),direction='warm energetic conversational; no pitch or rate processing',auditoryReview='unverified')
 receipt.write_text(json.dumps(result,indent=2),encoding='utf8');return result
if __name__=='__main__':
 data=json.loads(Path(__file__).with_name('script.json').read_text(encoding='utf8'));cues=data['cues']
 if len(sys.argv)>1 and sys.argv[1]!='all':cues=[x for x in cues if x['id'] in sys.argv[1:]]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for result in pool.map(run,cues):
   print(json.dumps(result),flush=True)
   if result.get('failed'):raise SystemExit('Voice service rejected request; no quota-exhaustion fallback')
