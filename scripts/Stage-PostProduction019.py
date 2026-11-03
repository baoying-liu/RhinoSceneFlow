"""Gracefully upgrade our idle local Web service; preserve all user projects and add an owned example."""
import json,os,shutil,subprocess,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=Path(os.environ['LOCALAPPDATA'])/'RhinoSceneFlow/postproduction'
service=json.loads((data/'service.json').read_text())
base='http://127.0.0.1:'+str(service['port'])
def api(route,body=None):
 headers={'Authorization':'Bearer '+service['token']}
 if body is not None:body=json.dumps(body).encode();headers['Content-Type']='application/json'
 with urllib.request.urlopen(urllib.request.Request(base+'/api'+route,data=body,headers=headers),timeout=30) as response:return json.loads(response.read())
assert api('/status')['service']=='RhinoSceneFlow.PostProduction'
for item in api('/projects'):
 assert not api('/projects/'+item['id'])['activeJobs'],'An existing user task must finish before service update'
api('/shutdown',{})
subprocess.run(['powershell','-NoProfile','-Command',f"Wait-Process -Id {int(service['pid'])} -Timeout 20 -ErrorAction SilentlyContinue"],capture_output=True)
backup=data.parent/'postproduction-backups'/('Before019-'+time.strftime('%Y%m%d-%H%M%S'))
shutil.copytree(data/'projects',backup/'projects')
source=ROOT/'artifacts/postproduction-images/6037710ff7834f34b12138d30b79a723'
receipt=json.loads((source/'batch-request.json').read_text())
project=receipt['project'];target=data/'projects'/project
assert not target.exists(),'Do not replace an existing project'
shutil.copytree(source/'projects'/project,target)
state=json.loads((target/'project.json').read_text(encoding='utf-8'))
state.update(name='AI 后期示例 · 山地建筑',created=time.time(),latestRun=receipt['batch'])
(target/'project.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
report=dict(backup=str(backup),exampleProject=project,exampleRun=receipt['batch'],userProjectsPreserved=True)
folder=ROOT/'artifacts/rhino-B/postproduction019';folder.mkdir(parents=True,exist_ok=True)
(folder/'staged.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
