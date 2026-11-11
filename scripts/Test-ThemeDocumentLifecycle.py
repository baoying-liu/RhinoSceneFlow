"""B-only document transitions with all eight tools attached. No model calls."""
import importlib.machinery,json,time
from pathlib import Path
m=importlib.machinery.SourceFileLoader('audit',str(Path(__file__).resolve().parents[1]/'scripts/Audit-UX20261110.py')).load_module()
out=Path('artifacts/theme-ui-0227')
stateSource="""import Rhino,System,json,clr
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
d=Rhino.RhinoDoc.ActiveDoc
r=json.loads(McpApi.Execute('{"apiVersion":1,"operation":"material_workspace_status"}'))
if not r['ok']:
 assert r['error']['message']=='文档已关闭。',r
 print('UX_AUDIT:'+json.dumps(dict(retry=True)))
else:
 print('UX_AUDIT:'+json.dumps(dict(pid=EXPECTED_PID,serial=int(d.RuntimeSerialNumber),path=d.Path,objects=d.Objects.Count,modified=d.Modified,tools={k:dict(document=v['document'],error=v['error']) for k,v in r['result']['tools'].items()})))
"""
before=m.run(stateSource);assert not before['modified'] and before['objects']==70;pid=before['pid'];serial=before['serial'];transitions=[]
for action in ('new','new','open'):
 command='_-New _None' if action=='new' else '_-Open "'+before['path']+'" _Enter'
 source="""import Rhino,System,json
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
assert not Rhino.RhinoDoc.ActiveDoc.Modified
assert Rhino.RhinoApp.RunScript(COMMAND,False)
print('UX_AUDIT:'+json.dumps(dict(issued=True)))
""".replace('COMMAND',repr(command))
 try:m.run(source);reset=False
 except (ConnectionResetError,ConnectionAbortedError):reset=True
 after=None
 for attempt in range(30):
  try:
   after=m.run(stateSource)
   if not after.get('retry') and after['serial']!=serial and len(after['tools'])==8 and all(t['document']==after['serial'] and t['error'] is None for t in after['tools'].values()):break
  except (ConnectionResetError,ConnectionAbortedError):pass
  time.sleep(.3)
 else:raise AssertionError('Tools did not rebind')
 assert after['pid']==pid and not after['modified'];transitions.append(dict(action=action,before=serial,after=after['serial'],samePid=True,allToolsRebound=True,platformResetAfterOpen=reset));serial=after['serial']
assert after['objects']==before['objects'] and after['path']==before['path']
r=dict(pid=pid,transitions=transitions,caseRestored=True,objects=after['objects'],modified=after['modified'],modelCalls=0)
(out/'lifecycle-verified.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
