"""Start the prepared Web payload independently of Rhino; same persisted service as the native Tool."""
import argparse,json,os,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--deployment',required=True);parser.add_argument('--codex',required=True);args=parser.parse_args()
data=Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/postproduction'
script=Path(args.deployment).resolve()/'PostProduction/server.py';assert script.is_file()
log=(data/'service019.log').open('a',encoding='utf-8')
child=subprocess.Popen([sys.executable,'-I','-X','utf8',str(script),'--data',str(data),'--codex',args.codex],stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
for _ in range(150):
 service=json.loads((data/'service.json').read_text())
 try:
  request=urllib.request.Request('http://127.0.0.1:'+str(service['port'])+'/api/status',headers={'Authorization':'Bearer '+service['token']})
  with urllib.request.urlopen(request,timeout=1) as response:status=json.loads(response.read())
  if status['version']=='0.19.0':break
 except OSError:pass
 assert child.poll() in (None,0),'Web startup failed; see service019.log'
 time.sleep(.1)
else:raise AssertionError('Prepared Web workbench was not ready')
staged=json.loads((ROOT/'artifacts/rhino-B/postproduction019/staged.json').read_text())
request=urllib.request.Request('http://127.0.0.1:'+str(service['port'])+'/api/projects/'+staged['exampleProject']+'/runs/'+staged['exampleRun'],headers={'Authorization':'Bearer '+service['token']})
with urllib.request.urlopen(request) as response:state=json.loads(response.read())
assert state['status']=='completed' and state['output']
receipt=dict(status=status,project=staged['exampleProject'],run=staged['exampleRun'],preparedWebHealthy=True)
(ROOT/'artifacts/rhino-B/postproduction019/web-ready.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt))
