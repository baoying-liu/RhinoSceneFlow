"""B-only native dock workspace and non-destructive fixture setup; no pointer input."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'workspace013');os.makedirs(folder,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
before=dict(objects=[str(o.Id) for o in doc.Objects],views=doc.NamedViews.Count,library=api('material_library')['directory'])
source=api('material_library')['assets'];assert len(source)>0
root=os.path.join(folder,'library');api('material_configure',directory=root)
if len(api('material_library')['assets'])==0:
 chosen=next((a for a in source if 'Limestone' in a['name']),source[0]);p=os.path.join(before['library'],'assets',chosen['id'].replace('-',''),chosen['maps']['baseColor'])
 a=api('material_import',asset=dict(name='浅灰石灰岩',category='石材',tags=['自然','粗糙','浅灰'],prompt='浅灰天然石灰岩，细腻均匀，无接缝，哑光',widthMeters=1,heightMeters=1),files=dict(baseColor=p))
 b=api('material_import',asset=dict(name='石灰岩 浅灰自然哑光',category='天然石头',tags=['天然','哑光','灰色'],prompt='浅灰天然石灰岩，哑光',widthMeters=1,heightMeters=1),files=dict(baseColor=p))
else:a,b=api('material_library')['assets'][:2]
layer=Rhino.DocObjects.Layer();layer.Name='SceneFlow_UI013_Fixture';layerIndex=doc.Layers.FindByFullPath(layer.Name,-1)
if layerIndex<0:layerIndex=doc.Layers.Add(layer)
ids=[]
for i in range(2):
 attrs=Rhino.DocObjects.ObjectAttributes();attrs.LayerIndex=layerIndex;attrs.Name='UI013_'+str(i)
 existing=next((o for o in doc.Objects if o.Attributes.Name==attrs.Name),None)
 if existing:ids.append(str(existing.Id));continue
 mesh=Rhino.Geometry.Mesh.CreateFromBox(Rhino.Geometry.BoundingBox(Rhino.Geometry.Point3d(i*2000,0,0),Rhino.Geometry.Point3d(i*2000+1000,1000,1000)),1,1,1)
 ids.append(str(doc.Objects.AddMesh(mesh,attrs)));mesh.Dispose()
doc.Objects.UnselectAll();doc.Objects.FindId(System.Guid(ids[0])).Select(True)
if doc.NamedViews.Count==0:doc.NamedViews.Add('SceneFlow_UI013',doc.Views.ActiveView.ActiveViewport.Id)
api('material_workspace_group')
for page in ['materials','uv','planting','export']:
 state=api('material_workspace_open',page=page)
 assert len(state['pages'])==4,state
assert all(len(p['dockBars'])>0 for p in state['pages']),state
assert len(set(p['dockBars'][0] for p in state['pages']))==1,state
api('material_workspace_open',page='materials');api('material_tool_select',assetId=a['id']);api('material_shelf_open',visible=True)
captureBefore=(doc.Objects.Count,doc.Modified,str(doc.Views.ActiveView.ActiveViewport.CameraLocation),len(doc.Views.GetViewList(True,True)))
preview=api('material_native_preview',assetId=a['id'],path=os.path.join(folder,'sphere-native.png'))
assert captureBefore==(doc.Objects.Count,doc.Modified,str(doc.Views.ActiveView.ActiveViewport.CameraLocation),len(doc.Views.GetViewList(True,True)))
report=dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),before=before,objects=ids,assets=[a['id'],b['id']],state=api('material_workspace_status'),preview=preview)
with open(os.path.join(folder,'setup.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
