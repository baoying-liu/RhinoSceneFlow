"""Export actual new AI material + shadow + Arctic using the docked workbench's async action."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,ExportPanelController
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'workspace013');fixture=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert not api('material_quick_status')['busy']
if not any(o.Attributes.Name=='UI013_Ground' for o in doc.Objects):
 attrs=Rhino.DocObjects.ObjectAttributes();attrs.Name='UI013_Ground'
 mesh=Rhino.Geometry.Mesh();[mesh.Vertices.Add(*v) for v in [(-1000,-2000,-20),(5000,-2000,-20),(5000,3000,-20),(-1000,3000,-20)]];mesh.Faces.AddFace(0,1,2,3);mesh.Normals.ComputeNormals();doc.Objects.AddMesh(mesh,attrs);mesh.Dispose()
v=doc.Views.ActiveView.ActiveViewport;v.SetCameraLocations(Rhino.Geometry.Point3d(1500,500,200),Rhino.Geometry.Point3d(5500,-6500,5000));v.ZoomBoundingBox(Rhino.Geometry.BoundingBox(Rhino.Geometry.Point3d(-1000,-2000,-20),Rhino.Geometry.Point3d(5000,3000,1000)))
index=doc.NamedViews.Add('SceneFlow_UI013',v.Id);viewId=str(doc.NamedViews[index].NamedViewId)
sun=doc.RenderSettings.Sun;sun.BeginChange(Rhino.Render.RenderContent.ChangeContexts.Program)
try:sun.ManualControlOn=True;sun.Enabled=True;sun.Azimuth=135;sun.Altitude=45
finally:sun.EndChange()
api('material_workspace_open',page='export');p=ExportPanelController.Find(doc.RuntimeSerialNumber);p.RefreshNamedViews()
row=next(r.Copy() for r in p.Views if str(r.Id)==viewId);row.Width=320;row.Height=240
from RhinoSceneFlow.Plugin import ExportLayerSetting
shadow=ExportLayerSetting();shadow.Kind='shadow';shadow.Blend='mul ';shadow.Opacity=75
texture=ExportLayerSetting();texture.Kind='texture'
arctic=ExportLayerSetting();arctic.Kind='display';arctic.Mode=System.Guid(next(m['id'] for m in api('workbench_settings')['displayModes'] if m['name']=='Arctic'))
row.Layers.Clear();row.Layers.Add(shadow);row.Layers.Add(texture);row.Layers.Add(arctic);p.SetView(row)
flags=BindingFlags.Instance|BindingFlags.NonPublic;p.GetType().GetField('folder',flags).GetValue(p).Text=os.path.join(folder,'exports-'+str(System.Guid.NewGuid())[:8])
state=(doc.Objects.Count,doc.Modified,str(v.CameraLocation),int(sun.Hash))
System.AppDomain.CurrentDomain.SetData('Workspace013ExportBefore',json.dumps(state));task=p.StartExport();System.AppDomain.CurrentDomain.SetData('Workspace013ExportTask',task)
print(json.dumps(dict(started=True,view=viewId,completed=task.IsCompleted,state=p.GetState().ToString())))
