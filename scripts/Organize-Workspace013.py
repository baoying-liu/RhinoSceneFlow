"""Run the real shelf button against this test library; capture metadata/binding invariants."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'workspace013')
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
state=api('material_quick_status');assert not state['busy'],state
job=api('material_chat_status',jobId=state['lastJob']);assert job['status']=='completed' and job['material'] and job['imagePath'],job
assets=api('material_library')['assets'];created=next(a for a in assets if a['id']==job['material']);assert created['category']!='待分类' and len(created['tags'])>=1,created
api('material_tool_apply')
report=dict(pid=EXPECTED_PID,generated=job,asset=created,assets=assets,geometry=[(str(o.Id),int(o.Geometry.DataCRC(0))) for o in doc.Objects],materials=[(str(o.Id),str(o.GetRenderMaterial(True).Id) if o.GetRenderMaterial(True) else None) for o in doc.Objects])
with open(os.path.join(folder,'generation-verified.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
