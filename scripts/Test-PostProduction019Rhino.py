"""Public MCP bridge only; no image quota, geometry changes or OS input."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__
folder=os.path.join(OUTPUT_DIR,'postproduction019');os.makedirs(folder,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
assert api('describe')['version']=='0.19.0'
before=(doc.Objects.Count,doc.Modified)
api('material_workspace_open',page='post')
job=api('postproduction_request',route='/api/status')
json.dump(dict(job=job['id'],document=int(doc.RuntimeSerialNumber),objects=before[0],modified=before[1]),open(os.path.join(folder,'bridge.json'),'w'),indent=2)
assert (doc.Objects.Count,doc.Modified)==before
print(json.dumps(dict(job=job['id'],panelHealthy=True)))
