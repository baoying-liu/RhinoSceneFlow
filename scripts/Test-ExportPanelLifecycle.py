import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import ExportPanelController
a=__rhino_doc__;assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
ids=[];before=a.Modified
try:
 for n in range(2):
  v=Rhino.DocObjects.ViewInfo(a.Views.ActiveView.ActiveViewport);v.Name='UI_Lifecycle_'+str(System.Guid.NewGuid())[:8];i=a.NamedViews.Add(v);ids.append(a.NamedViews[i].NamedViewId);v.Dispose()
 for n in range(3):
  p=ExportPanelController.Open(a);p.Close()
 print(json.dumps(dict(pid=EXPECTED_PID,rapidOpenClose=3,returned=True)))
finally:
 for i in range(a.NamedViews.Count-1,-1,-1):
  if a.NamedViews[i].NamedViewId in ids:a.NamedViews.Delete(i)
 a.Modified=before
