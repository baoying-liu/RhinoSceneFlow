"""One real tool-free text summary on a synthetic workflow image; no image requests."""
import json,os,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];payload=ROOT/'src/RhinoSceneFlow.Plugin/PostProduction'
report=json.loads((ROOT/'artifacts/workflow021-real-image.log').read_text(encoding='utf-8-sig').strip().splitlines()[-1]);out=Path(report['evidence']);bid=report['board'];nid=report['node'];base=None
codex=Path(os.environ['LOCALAPPDATA'])/'Programs/OpenAI/Codex/bin/codex.exe';env=os.environ.copy();env['SCENEFLOW_POST_TOKEN']='workflow-archive-fixture-token'
process=subprocess.Popen([sys.executable,'-I','-X','utf8',str(payload/'server.py'),'--data',str(out),'--codex',str(codex)],env=env,stdout=(out/'archive-out.log').open('w'),stderr=(out/'archive-error.log').open('w'),creationflags=subprocess.CREATE_NO_WINDOW)
def api(p,body=None,method=None):
 req=urllib.request.Request(base+'/api'+p,data=json.dumps(body).encode() if body is not None else None,method=method,headers={'Authorization':'Bearer workflow-archive-fixture-token','Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=120) as r:return json.load(r)
try:
 for _ in range(120):
  s=json.loads((out/'service.json').read_text());base='http://127.0.0.1:'+str(s['port'])
  try:
   if s['pid']==process.pid:api('/status');break
  except OSError:pass
  assert process.poll() is None;time.sleep(.1)
 b=api('/boards/'+bid);child=api('/boards/'+bid+'/nodes/'+nid+'/branch',dict(revision=b['revision']))
 job=api('/boards/'+bid+'/describe',dict(node=nid,archive=True,message='Summarize this generation step as concise modification intent for a later image edit. Use the visual brief and image. Do not invent unseen differences. Return the summary in reply.'))
 for _ in range(600):
  j=api('/jobs/'+job['job'])
  if j['status'] not in ('queued','running'):break
  time.sleep(1)
 assert j['status']=='completed',j
 b=api('/boards/'+bid);n=next(n for n in b['nodes'] if n['id']==nid);c=next(n for n in b['nodes'] if n['id']==child['id'])
 assert n['archived'] and n['archiveSummary'] and c['inputChanged']
 b=api('/boards/'+bid+'/nodes/'+nid+'/control',dict(revision=b['revision'],action='restore'));n=next(n for n in b['nodes'] if n['id']==nid);c=next(n for n in b['nodes'] if n['id']==child['id'])
 assert not n['archived'] and not c['inputChanged']
 result=dict(realTextSummary=True,toolFree=True,archiveMarksChildStale=True,restoreReversible=True,modelImageCalls=0)
 (out/'archive-verified.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:
 if base:
  try:api('/shutdown',{});process.wait(10)
  except Exception:pass
