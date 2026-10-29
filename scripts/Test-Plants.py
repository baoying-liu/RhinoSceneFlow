import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;assert doc.Objects.Count==0,'Fresh empty B document required'
folder=os.path.join(OUTPUT_DIR,'plants015');os.makedirs(folder,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.15.0'
original=api('material_library')['directory'];oldSettings=api('plant_settings');library=os.path.join(folder,'library-'+str(EXPECTED_PID));api('material_configure',directory=library)
doc.ModelUnitSystem=Rhino.UnitSystem.Meters
assets=[];objects=[]
for i,(species,name) in enumerate([('Acer rubrum','Red maple fixture'),('Acer palmatum','Japanese maple fixture')]):
 source='https://plants.ces.ncsu.edu/plants/'+species.lower().replace(' ','-')+'/'
 path=os.path.abspath(os.path.join(OUTPUT_DIR,'..','plant-fixtures','plant'+str(i)+'.png'))
 asset=api('plant_import',path=path,asset=dict(name=name,category='Sapindaceae',tags=['fixture','tree'],heightMeters=4,plant=dict(scientificName=species,family='Sapindaceae',genus='Acer',sources=[source],evidence='Synthetic alpha fixture; not AI botanical imagery.')));assets.append(asset)
 points=[[-2,0,0],[-1,1,0],[0,2,0]] if i==0 else [[-1,0,0],[1,1,0]]
 objects+=api('plant_place',assetId=asset['id'],points=points,seed=71+i,minScale=.9,maxScale=1.1,mirror=True)['objects']
# Opaque non-plant wall in front, and a scatter region behind.
points=[Rhino.Geometry.Point3d(0,-.5,0),Rhino.Geometry.Point3d(4,-.5,0),Rhino.Geometry.Point3d(4,-.5,2.2),Rhino.Geometry.Point3d(0,-.5,2.2)]
wall=Rhino.Geometry.Brep.CreateFromCornerPoints(*points,doc.ModelAbsoluteTolerance);attrs=Rhino.DocObjects.ObjectAttributes();attrs.Name='SceneFlowPlantWall';wallId=str(doc.Objects.AddBrep(wall,attrs));wall.Dispose()
plane=Rhino.Geometry.PlaneSurface(Rhino.Geometry.Plane(Rhino.Geometry.Point3d(0,5,0),Rhino.Geometry.Vector3d.ZAxis),Rhino.Geometry.Interval(-3,3),Rhino.Geometry.Interval(-2,2));attrs.Name='SceneFlowPlantScatterRegion';surface=str(doc.Objects.AddSurface(plane,attrs));plane.Dispose()
scatter=api('plant_scatter',assetId=assets[0]['id'],surfaceId=surface,count=8,spacingMeters=.8,seed=123,minScale=.2,maxScale=.3,mirror=True);assert scatter['placed']==8,scatter
assert len(api('plant_instances')['objects'])==13
vp=doc.Views.ActiveView.ActiveViewport;vp.SetProjection(Rhino.Display.DefinedViewportProjection.Perspective,'Plant015',True);vp.SetCameraLocations(Rhino.Geometry.Point3d(0,1,2),Rhino.Geometry.Point3d(9,-16,9));vp.ZoomExtents()
info=Rhino.DocObjects.ViewInfo(vp);info.Name='Plant015 Perspective';idx=doc.NamedViews.Add(info);view=str(doc.NamedViews[idx].NamedViewId);info.Dispose()
api('plant_settings',settings=dict(mode='auto',angle=60,transition=5))
rows=WorkbenchService.Settings(doc);row=next(r for r in rows if str(r.Id)==view);row.Width=600;row.Height=400
rendered=next(m for m in api('workbench_settings')['displayModes'] if m['name']=='Rendered');row.Mode=System.Guid(rendered['id'])
preview=WorkbenchService.Preview(doc,row,720);preview.Save(os.path.join(folder,'native-first.png'),System.Drawing.Imaging.ImageFormat.Png);preview.Dispose()
# Exactly one real new image through the SAME production material chat endpoint.
job=api('material_chat_start',conversation='请实际生成一株美国红枫 Acer rubrum 的完整夏季绿叶单株素材，透明背景 PNG，树形自然，参考高度 6 米。先核实真实植物。不需要地面、花盆或阴影。',reuseSimilar=False)
setup=dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),originalLibrary=original,oldSettings=oldSettings,library=library,assets=assets,objects=objects,wall=wallId,surface=surface,scatter=scatter,view=view,aiJob=job['id'])
with open(os.path.join(folder,'setup.json'),'w') as f:json.dump(setup,f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,planted=13,scatterSpacing=.8,realAiJob=job['id'],native=os.path.join(folder,'native-first.png'))))
