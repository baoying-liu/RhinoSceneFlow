"""Owned-case Studio audit through the ORIGINAL Rhino Platform on sandbox B.
No desktop input. No bearer is read, printed or stored by this client.
"""
import json,os,sys,time,uuid,subprocess,urllib.request,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class StudioMcp:
 def __init__(self,out):
  self.out=Path(out);self.out.mkdir(parents=True,exist_ok=True)
  s=json.loads(subprocess.check_output([sys.executable,str(ROOT/'scripts/Sandbox-Mcp.py'),'workspace_status']))
  assert s['ChannelId'] in ('1cee488700ad42f59492743cc4a2a3fe','0d327c4c84f644f089b73834ffd93cfe') and s.get('Pid'),'A known sandbox B must be running'
  m=json.loads((Path(s['LastStartupDirectory'])/'monitor-status.json').read_text(encoding='utf-8-sig'))
  assert m['Pid']==s['Pid'] and m['PlatformAllowed'];self.pid=s['Pid'];self.port=m['Port']
 def native(self,operation,**kw):
  payload=json.dumps(dict(apiVersion=1,operation=operation,**kw),ensure_ascii=True)
  source="import System,clr\nclr.AddReference('RhinoSceneFlow.Plugin')\nfrom RhinoSceneFlow.Plugin import McpApi\nassert System.Diagnostics.Process.GetCurrentProcess().Id=="+str(self.pid)+"\nprint('SF_AUDIT:'+McpApi.Execute("+repr(payload)+"))"
  body=dict(jsonrpc='2.0',id=1,method='tools/call',params=dict(name='run_python',arguments=dict(script=source)))
  req=urllib.request.Request('http://127.0.0.1:'+str(self.port)+'/',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'})
  r=json.load(urllib.request.urlopen(req,timeout=60))
  for c in r.get('result',{}).get('content',[]):
   for line in c.get('text','').splitlines():
    if line.startswith('SF_AUDIT:'):
     value=json.loads(line[len('SF_AUDIT:'):])
     if not value.get('ok'):raise RuntimeError(str(value)[:800])
     return value['result']
  raise RuntimeError('Original Platform returned no SceneFlow result: '+str(r)[:600])
 def api(self,route,body=None,method=None):
  started=time.monotonic();args=dict(route='/api'+route,method=method or ('POST' if body is not None else 'GET'))
  if body is not None:args['body']=body
  job=self.native('postproduction_request',**args)
  while time.monotonic()-started<240:
   try:state=self.native('postproduction_status',jobId=job['id'])
   except (ConnectionResetError,ConnectionAbortedError):
    # Platform can recycle its connection just after New/Open. Poll the same
    # recorded job; never repeat the original request, which may be a mutation.
    time.sleep(.25);continue
   if state['status']=='completed':
    with (self.out/'mcp-requests.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(dict(route=route,method=args['method'],seconds=round(time.monotonic()-started,3)))+'\n')
    return state['response']
   if state['status']=='failed':raise RuntimeError(state.get('error') or state.get('stage'))
   time.sleep(.25)
  raise TimeoutError('MCP request timeout; retained job '+job['id'])
 def board(self,bid):return self.api('/boards/'+bid)
 def patch(self,bid,**kw):return self.api('/boards/'+bid,dict(revision=self.board(bid)['revision'],**kw),'PUT')
 def branch(self,bid,node,sibling=False,stage='whole'):
  return self.api(f'/boards/{bid}/nodes/{node}/branch',dict(revision=self.board(bid)['revision'],sibling=sibling,stage=stage))
 def control(self,bid,node,action,**kw):return self.api(f'/boards/{bid}/nodes/{node}/control',dict(revision=self.board(bid)['revision'],action=action,**kw))
 def preflight(self,bid,node,stage='whole'):return self.api(f'/boards/{bid}/nodes/{node}/preflight',dict(revision=self.board(bid)['revision'],stage=stage))
 def generate(self,bid,node,stage='whole'):return self.api('/boards/'+bid+'/generate',dict(revision=self.board(bid)['revision'],node=node,stage=stage))

def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))

if __name__=='__main__':
 command=sys.argv[1];latest=ROOT/'artifacts/feature-audit-20261109/latest.json'
 if command=='init':
  out=latest.parent/uuid.uuid4().hex;client=StudioMcp(out);status=client.api('/status');assert status['version']=='0.22.1'
  prefs=client.api('/board-preferences');existing=client.api('/boards');source=ROOT/'artifacts/examples/Hillside-Retreat/PSD/01 Hillside Axon.psd'
  record=dict(folder=str(out),pid=client.pid,port=client.port,preferences=prefs,existingBoards=existing,source=str(source),sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),created=time.time(),checks=[])
  b=client.api('/boards',dict(name='Hillside · 完整功能测试 · 2026-11-09'));bid=b['id'];record['board']=bid
  n=client.api('/boards/'+bid+'/import-path',dict(path=str(source)))['node'];record['sourceNode']=n['id']
  prompt='Refine this architectural landscape axonometric into a polished daylight architectural visualization. Preserve the exact three building masses, roof shapes, existing openings, camera, paths, terrain silhouette, white background and every tree location. Improve surface appearance: warm off-white mineral walls, fine vertical weathered cedar boards, believable blue-grey glass, natural varied grass. Soft directional daylight. Do not add people, text, buildings, vegetation or redesign. Follow the protected-pixel mask.'
  roles={l['id']:'preserve' for l in n['source']['layers'] if l['name']=='Betula nigra'}
  client.patch(bid,nodes=[dict(id=n['id'],params={**n['params'],'prompt':prompt,'detail':65,'freedom':10,'roles':roles,'blend':100})])
  a=client.branch(bid,n['id']);record['wholeA']=a['id'];plan=client.preflight(bid,a['id']);write(out/'initial-preflight.json',plan);assert plan['ready'] and plan['input']['id']==n['id']
  task=client.generate(bid,a['id']);record['initialTask']=task['id'];record['initialJob']=task['job']
  write(latest,record);write(out/'session.json',record);print(json.dumps({k:record[k] for k in ['folder','board','sourceNode','wholeA','initialTask']},ensure_ascii=False))
 elif command=='poll':
  r=load(latest);c=StudioMcp(r['folder']);tasks=c.api('/boards/'+r['board']+'/tasks');write(Path(r['folder'])/'tasks.json',tasks);print(json.dumps([dict(id=t['id'],node=t['node'],stage=t['stage'],status=t['status'],phase=t['phase'],error=t.get('error')) for t in tasks],ensure_ascii=False))
 else:raise ValueError('init | poll')
