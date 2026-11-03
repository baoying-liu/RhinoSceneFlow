import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;assert doc.Objects.Count==0 and not doc.Modified
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert not api('plant_edit_status')['isolated']
ws=api('material_workspace_status');assert all(t['error'] is None for t in ws['tools'].values()),ws
json.dump(dict(pid=EXPECTED_PID,newFromIsolation=True,allToolsHealthy=True,editing=api('plant_edit_status')),open(os.path.join(OUTPUT_DIR,'plant-edit0171','new.json'),'w'),indent=2)
print('New from isolated editing passed')
