import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plants016');setup=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
state=api('plant_group_state',groupId=setup['group']);assert not state['busy'] and state['error'] is None,state
assert state['count']==60 and state['manual']==2,state
assert doc.Objects.Count==2,doc.Objects.Count
objects=api('plant_instances')['objects'];assert len(objects)==60
assert all(abs(p['position']['z'])<1e-6 for p in objects)
with open(os.path.join(folder,'baseline.json'),'w') as f:json.dump(dict(state=state,objects=objects),f,indent=2)
print(json.dumps(dict(count=state['count'],manual=state['manual'],singleObject=True,status=api('material_workspace_status'))))
