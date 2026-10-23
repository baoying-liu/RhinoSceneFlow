import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import ExportPanelController
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__
def state():
 v=doc.Views.ActiveView.ActiveViewport
 return (doc.Modified,str(v.CameraLocation),str(v.CameraDirection),str(v.Size),v.Name,str(v.DisplayMode.Id),int(doc.RenderSettings.Sun.Hash),tuple((str(w.MainViewport.Id),w.Floating) for w in doc.Views.GetViewList(True,True)))
before=state()
for i in range(3):
 p=ExportPanelController.Find(doc.RuntimeSerialNumber)
 if p is not None:p.Close()
 p=ExportPanelController.Open(doc)
 for r in p.Views:p.RefreshCard(r.Id)
 assert state()==before
p.Close()
assert state()==before
result=dict(ok=True,pid=EXPECTED_PID,cycles=3,viewsUnchanged=True,floatingViews=len([w for w in doc.Views.GetViewList(True,True) if w.Floating]),panelClosed=True)
with open(os.path.join(OUTPUT_DIR,'workbench','windows-verified.json'),'w') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
