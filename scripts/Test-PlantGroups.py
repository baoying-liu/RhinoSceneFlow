import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;assert doc.Objects.Count==0 and not doc.Modified
folder=os.path.join(OUTPUT_DIR,'plants016');os.makedirs(folder,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.16.0'
old=api('material_library')['directory'];setup=json.load(open(os.path.join(OUTPUT_DIR,'plants015','setup.json')))
api('material_configure',directory=setup['library']);assets=api('plant_library')['assets'];assert len(assets)>=2
doc.ModelUnitSystem=Rhino.UnitSystem.Meters
mesh=Rhino.Geometry.Mesh()
for y in range(11):
 for x in range(21):mesh.Vertices.Add(x,y,0)
for y in range(10):
 for x in range(20):
  a=y*21+x;mesh.Faces.AddFace(a,a+1,a+22,a+21)
mesh.Normals.ComputeNormals();surface=doc.Objects.AddMesh(mesh);mesh.Dispose()
palette=[dict(asset=assets[0]['id'],weight=1,spacingMeters=.7),dict(asset=assets[1]['id'],weight=3,spacingMeters=1.2)]
root=api('plant_group_create',spec=dict(name='Parametric planting test',surface=str(surface),palette=palette,settings=dict(density=.3)))['id']
api('plant_group_manual',groupId=root,assetId=palette[0]['asset'],point=[3,3,1])
api('plant_group_manual',groupId=root,assetId=palette[1]['asset'],point=[5,4,2])
api('material_workspace_group');api('material_workspace_open',page='planting');doc.Objects.UnselectAll();doc.Objects.Select(System.Guid(root));doc.Views.Redraw()
record=dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),surface=str(surface),group=root,palette=palette,originalLibrary=old,testLibrary=setup['library'])
with open(os.path.join(folder,'setup.json'),'w') as f:json.dump(record,f,indent=2)
print(json.dumps(record))
