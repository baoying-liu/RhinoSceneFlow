"""Resume preserved real image work after a service update; then reuse its style/accepted tile in a batch."""
import argparse,json,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--data',required=True);parser.add_argument('--codex',required=True);args=parser.parse_args()
folder=Path(args.data).resolve();record=json.loads((folder/'request.json').read_text());ident=record['project'];run=record['run']
service=json.loads((folder/'service.json').read_text())
def api(path,body=None):
 headers={'Authorization':'Bearer '+service['token']}
 if body is not None:body=json.dumps(body).encode();headers['Content-Type']='application/json'
 with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:'+str(service['port'])+'/api'+path,data=body,headers=headers),timeout=120) as response:return json.loads(response.read())
api('/shutdown',{})
subprocess.run(['powershell','-NoProfile','-Command',f"Wait-Process -Id {int(service['pid'])} -Timeout 15 -ErrorAction SilentlyContinue"],capture_output=True)
process=subprocess.Popen([sys.executable,'-I','-X','utf8',str(ROOT/'src/RhinoSceneFlow.Plugin/PostProduction/server.py'),'--data',str(folder),'--codex',args.codex],stdout=(folder/'resume-stdout.log').open('w'),stderr=(folder/'resume-stderr.log').open('w'),creationflags=subprocess.CREATE_NO_WINDOW)
for _ in range(200):
 service=json.loads((folder/'service.json').read_text())
 if service['pid']==process.pid:
  try:api('/status');break
  except OSError:pass
 assert process.poll() is None,(folder/'resume-stderr.log').read_text()
 time.sleep(.1)
def wait(job):
 previous=None
 for _ in range(3600):
  result=api('/jobs/'+job)
  if result['stage']!=previous:print(result['stage'],flush=True);previous=result['stage']
  if result['status'] not in ('queued','running'):
   assert result['status']=='completed',result
   return result
  time.sleep(.5)
 raise AssertionError('timeout')
before=len(list((folder/'projects'/ident/'runs').rglob('receipt.json')))
job=api('/projects/'+ident+'/runs/'+run+'/resume',{});wait(job['job'])
trial=api('/projects/'+ident+'/runs/'+run)
assert trial['output'] and trial['tiles'][0]['status']=='completed',trial
assert len(list((folder/'projects'/ident/'runs').rglob('receipt.json')))==before,'resume needlessly generated an accepted tile'
project=api('/projects/'+ident)
batch=api('/projects/'+ident+'/generate',dict(revision=project['revision'],mode='all',styleRunId=run))
write=dict(record,trial=run,batch=batch['run']);(folder/'batch-request.json').write_text(json.dumps(write,indent=2))
wait(batch['job'])
state=api('/projects/'+ident+'/runs/'+batch['run'])
assert state['style']['reusedFrom']==run and state['tiles'][0]['reusedFrom']==run,state
(folder/'batch-state.json').write_text(json.dumps(state,indent=2))
print(json.dumps(dict(folder=str(folder),project=ident,trial=run,batch=batch['run'],status=state['status'])))
