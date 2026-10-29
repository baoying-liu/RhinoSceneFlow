import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;assert doc.Objects.Count==0 and not doc.Modified
folder=os.path.join(OUTPUT_DIR,'plants015');setup=json.load(open(os.path.join(folder,'setup.json')));ai=json.load(open(os.path.join(folder,'ai-verified.json')))
examples=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Planting-v015'));os.makedirs(examples,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.15.0'
api('material_configure',directory=setup['originalLibrary']);before=api('plant_library')['assets']
published=os.path.join(folder,'published-asset.json')
if os.path.isfile(published):
 receipt=json.load(open(published));asset=next(a for a in before if a['id']==receipt['asset']['id'])
else:
 descriptor=ai['asset'];checked=json.load(open(os.path.abspath(os.path.join(OUTPUT_DIR,'..','plant-ai','resolved.json'))))
 assert checked['scientificName']==descriptor['plant']['scientificName']
 descriptor['plant']['sources']=checked['sources'];descriptor['plant']['verifiedUtc']=System.DateTime.UtcNow.ToString('o')
 asset=api('plant_import',asset=descriptor,path=ai['job']['imagePath'])
 after=api('plant_library')['assets'];assert set(a['id'] for a in after)==set(a['id'] for a in before)|{asset['id']}
 with open(published,'w') as f:json.dump(dict(asset=asset,originalLibrary=setup['originalLibrary'],addedOneRealPlantOnly=True,beforeCount=len(before)),f,indent=2)
png=os.path.join(examples,'Acer-rubrum-'+asset['id'][:8]+'.png')
if not os.path.exists(png):System.IO.File.Copy(ai['job']['imagePath'],png)
doc.ModelUnitSystem=Rhino.UnitSystem.Meters
objects=api('plant_place',assetId=asset['id'],points=[[-3,0,0],[0,2,0],[3,3,0],[-2,5,0]],seed=287,minScale=.65,maxScale=1.1,mirror=True)['objects']
def surface(points,name):
 b=Rhino.Geometry.Brep.CreateFromCornerPoints(*[Rhino.Geometry.Point3d(*p) for p in points],doc.ModelAbsoluteTolerance);a=Rhino.DocObjects.ObjectAttributes();a.Name=name;oid=doc.Objects.AddBrep(b,a);b.Dispose();return str(oid)
surface([[-6,-3,0],[6,-3,0],[6,8,0],[-6,8,0]],'Planting demo ground')
surface([[0,-1,0],[4,-1,0],[4,-1,3],[0,-1,3]],'Planting demo wall')
api('plant_settings',settings=dict(mode='auto',angle=60,transition=5))
views=[]
vp=doc.Views.ActiveView.ActiveViewport;vp.SetProjection(Rhino.Display.DefinedViewportProjection.Perspective,'Planting',True);vp.SetCameraLocations(Rhino.Geometry.Point3d(0,2,2.5),Rhino.Geometry.Point3d(14,-20,12));vp.ZoomBoundingBox(Rhino.Geometry.BoundingBox(Rhino.Geometry.Point3d(-8,-3,0),Rhino.Geometry.Point3d(8,12,8)))
info=Rhino.DocObjects.ViewInfo(vp);info.Name='Planting Perspective';i=doc.NamedViews.Add(info);views.append(str(doc.NamedViews[i].NamedViewId));info.Dispose()
top=Rhino.Display.RhinoViewport();top.Size=System.Drawing.Size(700,700);top.SetProjection(Rhino.Display.DefinedViewportProjection.Top,'Planting Top',True);top.ZoomBoundingBox(Rhino.Geometry.BoundingBox(Rhino.Geometry.Point3d(-8,-3,0),Rhino.Geometry.Point3d(8,14,1)))
info=Rhino.DocObjects.ViewInfo(top);info.Name='Planting Top';i=doc.NamedViews.Add(info);views.append(str(doc.NamedViews[i].NamedViewId));info.Dispose();top.Dispose()
rendered=Rhino.Display.DisplayModeDescription.RenderedId
for view in views:api('configure_view',viewId=view,settings=dict(width=1000,height=700,mode=str(rendered),layers=[dict(kind='plants',plantGrouping='species'),dict(kind='shadow',blend='mul '),dict(kind='texture')],plantShadows=True))
exports=api('export_workbench',directory=examples,views=views);assert all(f['ok'] for f in exports['files']),exports
for index,row in enumerate(WorkbenchService.Settings(doc)):
 b=WorkbenchService.Preview(doc,row,900);b.Save(os.path.join(examples,'preview-'+str(index)+'.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
options=Rhino.FileIO.FileWriteOptions();options.UpdateDocumentPath=True;options.SuppressDialogBoxes=True;model=os.path.join(examples,'Planting-Demo-'+str(EXPECTED_PID)+'.3dm');assert not os.path.exists(model);assert doc.WriteFile(model,options) and not doc.Modified
api('plant_select',assetId=asset['id']);state=api('material_workspace_status');assert all(t['error'] is None for t in state['tools'].values())
with open(os.path.join(folder,'delivery.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,asset=asset['id'],model=model,png=png,exports=exports,views=views,objects=objects,originalLibrary=setup['originalLibrary'],allToolsHealthy=True),f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,realPlant=asset['id'],model=model,exports=exports)))
