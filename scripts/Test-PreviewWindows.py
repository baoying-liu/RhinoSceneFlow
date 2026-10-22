"""No mouse: opening, previewing and closing must not create Rhino views/windows."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import ExportPanelController
from System.Reflection import BindingFlags
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__
def views():return sorted((str(v.MainViewport.Id),v.MainViewport.Name,v.Floating) for v in doc.Views.GetViewList(True,True))
def state():
 v=doc.Views.ActiveView.ActiveViewport
 return (doc.Modified,str(v.CameraLocation),str(v.CameraDirection),str(v.CameraUp),str(v.Size),str(v.DisplayMode.Id),v.Name,str(v.GetFrustum()),tuple(str(o.Id) for o in doc.Objects.GetSelectedObjects(False,False)))
p=ExportPanelController.Find(doc.RuntimeSerialNumber)
if p is not None:p.Close()
before=views();saved=state();assert doc.NamedViews.Count>0
for i in range(3):
 p=ExportPanelController.Open(doc)
 preview=p.GetType().GetField('preview',BindingFlags.Instance|BindingFlags.NonPublic).GetValue(p)
 assert str(preview.GetType().FullName)=='Eto.Forms.ImageView'
 p.RefreshPreview();assert views()==before and state()==saved,(views(),state(),saved)
 p.Close();assert views()==before and state()==saved
assert ExportPanelController.Find(doc.RuntimeSerialNumber) is None
report=dict(pid=EXPECTED_PID,cycles=3,viewsBefore=before,viewsAfter=views(),stateUnchanged=True,panelClosed=True)
with open(os.path.join(OUTPUT_DIR,'panel','windows-verified.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
