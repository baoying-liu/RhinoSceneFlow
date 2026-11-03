"""Create the three original demo views and save an owned office model before asset generation finishes."""
import Rhino,System,clr,json,os
from Rhino.Geometry import Point3d as P,BoundingBox
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,ExportPanelController,WorkbenchService
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.abspath(os.path.join(OUTPUT_DIR,'..','examples','Hillside-Retreat'))
data=json.load(open(os.path.join(folder,'geometry.json')))
assert int(doc.RuntimeSerialNumber)==data['document'] and all(o.Attributes.GetUserString('SceneFlow.Demo')=='HillsideRetreat.v1' for o in doc.Objects)
assert doc.NamedViews.Count==0,'Preserve existing named views'
vp=doc.Views.ActiveView.ActiveViewport;box=BoundingBox(P(-26,-20,-1),P(26,24,15))
for name,location,target,parallel in [('01 Hillside Axon',P(58,-75,57),P(0,2,3),True),('02 Arrival Perspective',P(35,-44,21),P(0,3,4),False),('03 Planting Overview',P(36,-39,76),P(0,2,1),True)]:
 vp.SetCameraLocations(target,location)
 if parallel:vp.ChangeToParallelProjection(True)
 else:vp.ChangeToPerspectiveProjection(True,40)
 vp.ZoomBoundingBox(box);vp.ConstructionGridVisible=False;vp.ConstructionAxesVisible=False;vp.WorldAxesIconVisible=False
 doc.NamedViews.Add(name,vp.Id)
sun=doc.Lights.Sun;sun.ManualControlOn=True;sun.Azimuth=135;sun.Altitude=42;sun.Enabled=True
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
api('material_workspace_open',page='export');ExportPanelController.Open(doc).RefreshNamedViews()
views=api('named_views');assert len(views)==3
doc.NamedViews.Restore(0,doc.Views.ActiveView,False);doc.Views.Redraw()
path=os.path.join(folder,'SceneFlow-Hillside-Retreat-Office.3dm');assert not os.path.exists(path),'Do not overwrite an existing demo'
options=Rhino.FileIO.FileWriteOptions();options.UpdateDocumentPath=True;options.SuppressDialogBoxes=True
assert doc.WriteFile(path,options) and not doc.Modified
with open(os.path.join(folder,'views.json'),'w') as f:json.dump(dict(model=path,views=views,pid=EXPECTED_PID),f,indent=2)
b=WorkbenchService.Preview(doc,WorkbenchService.Settings(doc)[0],1000);b.Save(os.path.join(folder,'geometry-preview.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
print(json.dumps(dict(model=path,views=len(views),objects=doc.Objects.Count)))
