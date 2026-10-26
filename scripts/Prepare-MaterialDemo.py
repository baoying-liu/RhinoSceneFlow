"""Prepare a fresh, owned material demo in B; refuses an existing nonempty model."""
import Rhino,System,clr,os,json
from Rhino.Geometry import Point3d,Vector3d,Plane,Interval,Brep,Box,Circle,Cylinder,BoundingBox
from System.Drawing import Color
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,MaterialPanelController
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;assert all(o.Attributes.GetUserString('SceneFlow.MaterialDemo')=='v0.7' for o in doc.Objects),'Demo requires an empty or owned demo model; no other geometry will be cleared.'
root=os.path.dirname(OUTPUT_DIR);folder=os.path.join(OUTPUT_DIR,'materials','demo');os.makedirs(folder,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
api('material_configure',directory=os.path.join(root,'materials','library-v07'))
ai=next((a for a in api('material_library')['assets'] if a['name']=='AI Limestone 1 m'),None)
if ai is None:
 job=api('material_generation_request',asset=dict(name='AI Limestone 1 m',category='Stone',tags=['ai','limestone'],widthMeters=1,heightMeters=1),prompt='Light warm-gray fine-grained limestone, neutral base color, 1 x 1 meter tile, no baked lighting.')
 ai=api('material_generation_complete',jobId=job['id'],files=dict(baseColor=os.path.join(root,'materials','source','ai-limestone-basecolor.png')))
latest=json.load(open(os.path.join(OUTPUT_DIR,'materials','latest.json')))
grid=api('material_import',asset=dict(name='Calibration 600 x 300 mm',category='Calibration',widthMeters=.6,heightMeters=.3),files=dict(baseColor=os.path.join(latest['folder'],'grid.png')))
scale=Rhino.RhinoMath.UnitScale(Rhino.UnitSystem.Meters,doc.ModelUnitSystem)
def p(x,y,z):return Point3d(x*scale,y*scale,z*scale)
ids=[];layer_ids=[]
def add(name,g,color):
 existing=next((o for o in doc.Objects if o.Attributes.Name==name and o.Attributes.GetUserString('SceneFlow.MaterialDemo')=='v0.7'),None)
 if existing is not None:
  id=existing.Id;assert doc.Objects.Replace(id,g);ids.append(id);layer_ids.append(doc.Layers[existing.Attributes.LayerIndex].Id);return str(id)
 l=Rhino.DocObjects.Layer();l.Name='SceneFlow_Materials_'+name;l.Color=Color.FromArgb(*color);li=doc.Layers.Add(l);layer_ids.append(doc.Layers[li].Id)
 a=Rhino.DocObjects.ObjectAttributes();a.Name=name;a.LayerIndex=li;a.SetUserString('SceneFlow.MaterialDemo','v0.7')
 id=doc.Objects.Add(g,a);assert id!=System.Guid.Empty;ids.append(id);return str(id)
floor=add('Limestone_1m',Brep.CreateFromCornerPoints(p(0,0,.05),p(4,0,.05),p(4,3,.05),p(0,3,.05),doc.ModelAbsoluteTolerance),(220,215,205))
box=add('Box_600x300',Box(Plane.WorldXY,Interval(5*scale,7*scale),Interval(0,2*scale),Interval(0,2*scale)).ToBrep(),(150,190,230))
cylinder=add('Cylinder_600x300',Cylinder(Circle(Plane(p(8.5,1,0),Vector3d.ZAxis),.6*scale),2.4*scale).ToBrep(True,True),(230,190,140))
api('material_apply',assetId=ai['id'],layers=[str(layer_ids[0])],mapping=dict(mode='plane'))
api('material_apply',assetId=grid['id'],objects=[box],mapping=dict(mode='box',alignment='object'))
api('material_apply',assetId=grid['id'],objects=[cylinder],mapping=dict(mode='cylinder'))
vp=doc.Views.ActiveView.ActiveViewport
vp.SetProjection(Rhino.Display.DefinedViewportProjection.Top,'Top',True);vp.ZoomBoundingBox(doc.Objects.BoundingBoxVisible)
info=Rhino.DocObjects.ViewInfo(vp);info.Name='Materials_Top';doc.NamedViews.Add(info);info.Dispose()
vp.SetProjection(Rhino.Display.DefinedViewportProjection.Perspective,'Perspective',True);vp.SetCameraLocations(p(4.5,1,1),p(13,-12,11));vp.ZoomBoundingBox(doc.Objects.BoundingBoxVisible)
info=Rhino.DocObjects.ViewInfo(vp);info.Name='Materials_Perspective';doc.NamedViews.Add(info);info.Dispose()
mode=Rhino.Display.DisplayModeDescription.FindByName('Rendered');vp.DisplayMode=mode
vp.ConstructionGridVisible=False;vp.ConstructionAxesVisible=False;vp.WorldAxesIconVisible=False;doc.Views.Redraw()
bitmap=doc.Views.ActiveView.CaptureToBitmap(System.Drawing.Size(1200,700),mode.DisplayAttributes);assert bitmap is not None
bitmap.Save(os.path.join(folder,'rendered.png'));bitmap.Dispose()
options=Rhino.FileIO.FileWriteOptions();options.SuppressDialogBoxes=True;options.UpdateDocumentPath=True
path=os.path.join(folder,'SceneFlow-Materials-Demo.3dm');assert doc.WriteFile(path,options)
panel=MaterialPanelController.Open(doc);panel.Select(System.Guid(ai['id']))
api('material_pack',assetId=ai['id'],path=os.path.join(folder,'limestone-'+str(System.Guid.NewGuid())[:8]+'.zip'))
report=dict(pid=EXPECTED_PID,library=api('material_library')['directory'],ai=ai,calibration=grid,objects=[str(i) for i in ids],model=path,capture=os.path.join(folder,'rendered.png'))
with open(os.path.join(folder,'ready.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,library=report['library'],model=path,capture=report['capture'])))
