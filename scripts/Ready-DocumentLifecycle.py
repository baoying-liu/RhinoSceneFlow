"""Post-restart check, preserving live geometry and selection."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.13.3'
s=api('material_workspace_group');serial=int(__rhino_doc__.RuntimeSerialNumber)
assert len(s['pages'])==5 and all(t['document']==serial and t['error'] is None for t in s['tools'].values()),s
report=dict(pid=EXPECTED_PID,version='0.13.3',document=serial,workspace=s)
with open(os.path.join(OUTPUT_DIR,'document-switch','ready.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,version='0.13.3',allToolsRebound=True,chat=s['tools']['materials']['details']['chatKit'])))
