"""Finish queued first apply, then change live selection and apply from the independent library."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'library0131');fixture=json.load(open(os.path.join(folder,'setup.json')))
assert int(doc.RuntimeSerialNumber)==fixture['document']
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert not api('material_panel_status')['busy']
first=api('material_inspect',objects=fixture['objects'][:1]);assert fixture['assets'][0] in json.dumps(first),first
assert all(v['status']['valid'] for v in api('material_uv_status',objects=fixture['objects'][:1]))
doc.Objects.UnselectAll();doc.Objects.FindId(System.Guid(fixture['objects'][1])).Select(True)
api('material_tool_select',page='library',assetId=fixture['assets'][1]);api('material_tool_apply',page='library')
with open(os.path.join(folder,'first.json'),'w') as f:json.dump(first,f,indent=2)
print(json.dumps(dict(firstApplyAndAutomaticUv=True,secondApplyStarted=True)))
