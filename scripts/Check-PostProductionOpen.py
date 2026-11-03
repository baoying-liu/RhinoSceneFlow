import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__
assert doc.Path.endswith('SceneFlow-Hillside-Retreat-PlantOutline-Fixed.3dm') and not doc.Modified
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_workspace_status'))));assert r['ok'],r
assert all(t['error'] is None for t in r['result']['tools'].values())
assert r['result']['tools']['post']['document']==int(doc.RuntimeSerialNumber)
json.dump(dict(pid=EXPECTED_PID,path=doc.Path,objects=doc.Objects.Count,modified=doc.Modified,document=int(doc.RuntimeSerialNumber),post=r['result']['tools']['post']),open(os.path.join(OUTPUT_DIR,'postproduction018','open.json'),'w'),indent=2)
print(json.dumps(dict(openHealthy=True,modified=doc.Modified,objects=doc.Objects.Count)))
