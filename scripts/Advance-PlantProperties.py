import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'properties017');record=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
group=record['group'];state=api('plant_group_state',groupId=group);assert not state['busy'] and state['error'] is None,state
obj=doc.Objects.FindId(System.Guid(group));rows=json.loads(obj.Geometry.UserDictionary.GetString('SceneFlow.PlantRows.v1'))
row=next(r for r in rows if r['id']==record['individual']);assert row['asset']==record['individualAsset'] and row['scale']==2.1 and row['mirror'] and abs(row['position']['z']-.8)<1e-5,row
assert len(rows)==record['initialCount'] and not any(r['id']==record['originalIndividual'] for r in rows)
selection=api('plant_list_select',groups=[group]);assert selection['selected']==[group],selection
assert doc.Objects.FindId(System.Guid(group)).IsSelected(False)>0
# Trigger genuine Eto list selection -> native document selection, without mouse.
from RhinoSceneFlow.Plugin import SceneFlowWorkspace
from System.Reflection import BindingFlags
flags=BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public
panel=Rhino.UI.Panels.GetPanel(System.Guid(api('material_workspace_status')['pages'][5]['panelId']))
tool=panel.GetType().GetProperty('Tool',flags).GetValue(panel);grid=tool.GetType().GetField('list',flags).GetValue(tool)
# WPF selection events are dispatched after this Platform script returns.
# Native deselection must propagate on the next UI tick.
doc.Objects.UnselectAll()
settings=state['spec']['settings'];settings.update(density=.08,layoutSeed=909,sizeSeed=910,mirrorSeed=911,minScale=.8,maxScale=1.8)
api('plant_group_update',groupId=group,settings=settings,palette=[p for p in record['palette'] if p['asset']!=record['individualAsset']])
source=doc.Objects.FindId(System.Guid(record['surface']));mesh=source.Geometry.DuplicateMesh()
for i in range(mesh.Vertices.Count):
 p=mesh.Vertices[i];mesh.Vertices.SetVertex(i,p.X,p.Y,p.Z+1)
mesh.Normals.ComputeNormals();doc.Objects.Replace(source.Id,mesh);mesh.Dispose()
record.update(changedAllSeeds=True,sourceMoved=True)
with open(os.path.join(folder,'setup.json'),'w') as f:json.dump(record,f,indent=2)
print('Custom instance/count/type verified; group seeds and carrier changed')
