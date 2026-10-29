"""Replace only the empty B test document while keeping the chosen library root."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
assert __rhino_doc__.Objects.Count==0
folder=os.path.join(OUTPUT_DIR,'shared-library0133')
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_library'))));assert r['ok'],r
with open(os.path.join(folder,'before-new.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,document=int(__rhino_doc__.RuntimeSerialNumber),library=r['result']['directory'],assets=[a['id'] for a in r['result']['assets']]),f,indent=2)
__rhino_doc__.Modified=False
assert Rhino.RhinoApp.RunScript('_-New _None',False)
