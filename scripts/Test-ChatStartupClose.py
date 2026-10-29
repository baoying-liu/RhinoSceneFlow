"""Build the AI tool and close its document immediately, before awaiting ChatKit startup."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
assert __rhino_doc__.Objects.Count==0
folder=os.path.join(OUTPUT_DIR,'document-switch')
before=int(__rhino_doc__.RuntimeSerialNumber)
assert Rhino.RhinoApp.RunScript('_-New _None',False)
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_workspace_open',page='materials'))));assert r['ok'],r
middle=int(Rhino.RhinoDoc.ActiveDoc.RuntimeSerialNumber)
with open(os.path.join(folder,'startup-close.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,before=before,middle=middle,chat=r['result']['tools']['materials']['details']['chatKit']),f,indent=2)
assert Rhino.RhinoApp.RunScript('_-New _None',False)
