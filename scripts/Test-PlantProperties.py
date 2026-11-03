"""B-only, empty-document fixture for list/selection/material scopes and persistent single plants."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__
assert doc.Objects.Count==0 and not doc.Modified,'Use a fresh empty B document'
folder=os.path.join(OUTPUT_DIR,'properties017');os.makedirs(folder,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.17.0'
for page in ['materials','library','uv','planting','export','plantsList','properties']:api('material_workspace_open',page=page)
state=api('material_workspace_status');assert len(state['pages'])==7 and all(t['error'] is None for t in state['tools'].values()),state
originalFile=os.path.join(folder,'original-library.txt')
originalLibrary=open(originalFile,encoding='utf-8').read() if os.path.exists(originalFile) else api('material_library')['directory']
if not os.path.exists(originalFile):
 with open(originalFile,'w',encoding='utf-8') as f:f.write(originalLibrary)
testLibrary=os.path.join(folder,'fixture-library');api('material_configure',directory=testLibrary)
assets=api('plant_library')['assets']
if len(assets)<2:
 for i,species in enumerate(['Acer rubrum','Acer palmatum']):
  path=os.path.abspath(os.path.join(OUTPUT_DIR,'..','plant-fixtures','plant'+str(i)+'.png'))
  api('plant_import',path=path,asset=dict(name=species+' test fixture',category='Sapindaceae',tags=['fixture'],heightMeters=4,plant=dict(scientificName=species,family='Sapindaceae',genus='Acer',names=dict(zh='测试植物'+str(i),en='Test plant '+str(i)),sources=['https://plants.ces.ncsu.edu/plants/'+species.lower().replace(' ','-')+'/'],evidence='Synthetic regression alpha fixture; not AI botanical imagery.')))
 assets=api('plant_library')['assets']
doc.ModelUnitSystem=Rhino.UnitSystem.Meters
la=doc.Layers.Add('SceneFlow 017 test A',System.Drawing.Color.Green);lb=doc.Layers.Add('SceneFlow 017 test B',System.Drawing.Color.Brown)
mesh=Rhino.Geometry.Mesh()
for p in [(0,0,0),(20,0,0),(20,20,2),(0,20,2)]:mesh.Vertices.Add(*p)
mesh.Faces.AddFace(0,1,2,3);mesh.Normals.ComputeNormals();surface=doc.Objects.AddMesh(mesh);mesh.Dispose()
palette=[dict(asset=a['id'],weight=1,spacingMeters=1) for a in assets[:2]]
group=api('plant_group_create',spec=dict(name='Properties 017 demo',surface=str(surface),palette=palette,settings=dict(density=.06)))['id']
api('plant_group_manage',groups=[group],name='Renamed group',layerId=str(doc.Layers[la].Id))
obj=doc.Objects.FindId(System.Guid(group));assert obj.Name=='Renamed group' and obj.Attributes.LayerIndex==la
api('plant_group_manage',groups=[group],visible=False);assert doc.Objects.FindId(System.Guid(group)).IsHidden
assert any(g['id']==group for g in api('plant_group_list')['groups'])
api('plant_group_manage',groups=[group],visible=True,locked=True);assert doc.Objects.FindId(System.Guid(group)).IsLocked
api('plant_group_manage',groups=[group],locked=False)
ids=[]
for x,layer in [(25,la),(28,la),(31,lb)]:
 b=Rhino.Geometry.Box(Rhino.Geometry.Plane.WorldXY,Rhino.Geometry.Interval(x,x+2),Rhino.Geometry.Interval(0,2),Rhino.Geometry.Interval(0,2)).ToBrep()
 attr=Rhino.DocObjects.ObjectAttributes();attr.LayerIndex=layer;ids.append(doc.Objects.AddBrep(b,attr));b.Dispose()
native=Rhino.DocObjects.Material();native.ToPhysicallyBased();native.PhysicallyBased.Roughness=.3
from Rhino.Render import RenderMaterial,RenderTexture
material=RenderMaterial.FromMaterial(native,doc);material.Name='Scope oracle';doc.RenderMaterials.Add(material);native.Dispose()
for id in ids:
 o=doc.Objects.FindId(id);o.RenderMaterial=material;o.CommitChanges()
report=api('selection_material_update',objects=[str(ids[0])],roughness=.42)
assert len(report['objects'])==3 and report['cloned']==0,report
report=api('selection_material_update',objects=[str(ids[0])],scope='object',roughness=.67)
assert report['cloned']==1,report
first=doc.Objects.FindId(ids[0]).GetRenderMaterial(True);second=doc.Objects.FindId(ids[1]).GetRenderMaterial(True)
assert first.Id!=second.Id
assert abs(first.ToMaterial(RenderTexture.TextureGeneration.Allow).PhysicallyBased.Roughness-.67)<1e-6
assert abs(second.ToMaterial(RenderTexture.TextureGeneration.Allow).PhysicallyBased.Roughness-.42)<1e-6
repeat=api('selection_material_update',objects=[str(ids[0])],scope='object',roughness=.71);assert repeat['cloned']==0,repeat
receipt=dict(pid=EXPECTED_PID,group=group,surface=str(surface),palette=palette,objects=[str(i) for i in ids],layer=str(doc.Layers[lb].Id),initialScopePassed=True,originalLibrary=originalLibrary,testLibrary=testLibrary)
with open(os.path.join(folder,'setup.json'),'w') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
