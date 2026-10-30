import Rhino,System,clr,json,os,math
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;assert doc.Objects.Count==0 and not doc.Modified
folder=os.path.join(OUTPUT_DIR,'plants016');examples=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Planting-v016'));os.makedirs(examples,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.16.0'
original=json.load(open(os.path.join(folder,'setup.json')))['originalLibrary'];api('material_configure',directory=original)
asset=next(a for a in api('plant_library')['assets'] if a['id']=='e55d4f7b-0f15-49e9-bddf-dd999c2d79b7')
botany=json.load(open(os.path.join(folder,'spacing-ai.json')));assert botany['scientificName']==asset['plant']['scientificName']
if asset['plant'].get('spacingMeters')!=botany['spacingMeters']:
 asset['plant']['spacingMeters']=botany['spacingMeters'];asset['plant']['spacingEvidence']=botany['spacingEvidence'];asset=api('plant_update',asset=asset)
doc.ModelUnitSystem=Rhino.UnitSystem.Meters
mesh=Rhino.Geometry.Mesh()
for y in range(11):
 for x in range(11):mesh.Vertices.Add(x*2,y*2,.8*math.sin(x*.45)*math.cos(y*.4))
for y in range(10):
 for x in range(10):
  a=y*11+x;mesh.Faces.AddFace(a,a+1,a+12,a+11)
mesh.Normals.ComputeNormals();attrs=Rhino.DocObjects.ObjectAttributes();attrs.Name='Editable planting terrain';attrs.LayerIndex=doc.Layers.Add('Terrain',System.Drawing.Color.FromArgb(230,230,230));surface=doc.Objects.AddMesh(mesh,attrs);mesh.Dispose()
root=api('plant_group_create',spec=dict(name='Acer rubrum planting',surface=str(surface),palette=[dict(asset=asset['id'],weight=1,spacingMeters=4)],settings=dict(density=.03,edgeDistance=2,edgeStrength=.35,edgeCurve=[0,.2,.6,.9,1])))['id']
for p in [[4,4,0],[14,14,0]]:api('plant_group_manual',groupId=root,assetId=asset['id'],point=p)
for page in ['materials','library','uv','export','planting']:api('material_workspace_open',page=page)
doc.Objects.UnselectAll();doc.Objects.Select(System.Guid(root));doc.Views.Redraw()
receipt=dict(pid=EXPECTED_PID,group=root,surface=str(surface),asset=asset['id'],library=original,examples=examples,spacingRecommendation=botany['spacingMeters'],compositionSpacing=4)
with open(os.path.join(folder,'delivery.json'),'w') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
