"""B-only independent library tool, shared state and live-selection regression. No pointer input."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'library0131');os.makedirs(folder,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
def field(o,n):return o.GetType().GetField(n,BindingFlags.Instance|BindingFlags.NonPublic).GetValue(o)
def tool(state,index):
 panel=Rhino.UI.Panels.GetPanel(System.Guid(state['pages'][index]['panelId']))
 return panel,panel.GetType().GetProperty('Tool',BindingFlags.Instance|BindingFlags.NonPublic).GetValue(panel)
assert api('describe')['version']=='0.13.3'
state=api('material_workspace_open',page='library');assert len(state['pages'])==5,state
libraryPanel,library=tool(state,1)
assert field(library,'chat') is None and field(library,'shelf') is not None
assets=api('material_library')['assets'];assert assets
a=assets[0];b=assets[-1]
api('material_tool_select',page='library',assetId=a['id'])
api('material_tool_settings',page='library',scope='layer')
state=api('material_workspace_open',page='materials');aiPanel,ai=tool(state,0)
assert field(ai,'chat') is not None and field(ai,'shelf') is None
assert not System.Object.ReferenceEquals(libraryPanel,aiPanel)
for page in ['library','materials']:
 s=api('material_workspace_status')['tools'][page]['details']
 assert s['selected']==a['id'] and s['scope']=='layer',s
api('material_tool_select',assetId=b['id'])
assert api('material_panel_status')['selected']==b['id']
api('material_tool_settings',scope='object')
assert api('material_panel_status')['scope']=='object'
originalSelection=[str(o.Id) for o in doc.Objects.GetSelectedObjects(False,False)]
ids=[]
for i in range(2):
 attrs=Rhino.DocObjects.ObjectAttributes();attrs.Name='SceneFlow_Library0131_'+str(i)
 mesh=Rhino.Geometry.Mesh.CreateFromBox(Rhino.Geometry.BoundingBox(Rhino.Geometry.Point3d(i*1600,0,0),Rhino.Geometry.Point3d(i*1600+1000,1000,1000)),1,1,1)
 ids.append(str(doc.Objects.AddMesh(mesh,attrs)));mesh.Dispose()
doc.Objects.UnselectAll();doc.Objects.FindId(System.Guid(ids[0])).Select(True)
api('material_tool_select',page='library',assetId=a['id'])
api('material_tool_apply',page='library')
report=dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),objects=ids,assets=[a['id'],b['id']],originalSelection=originalSelection,separateTools=True,libraryHasNoChat=True,sharedScope=True,sharedSelection=True,state=api('material_workspace_status'))
with open(os.path.join(folder,'setup.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,separateTools=True,libraryHasNoChat=True,sharedScope=True,sharedSelection=True,firstApplyStarted=True)))
