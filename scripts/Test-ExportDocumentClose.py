"""Build real Named View card/detail controls, then close their owned document."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import ExportPanelController
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;assert all(o.Attributes.Name.startswith('SceneFlow_Library0131_') for o in doc.Objects)
if doc.NamedViews.Count==0:doc.NamedViews.Add('Lifecycle_Export',doc.Views.ActiveView.ActiveViewport.Id)
p=ExportPanelController.Open(doc);p.RefreshNamedViews();assert p.Views.Count>0;p.OpenDetails(p.Views[0].Id)
with open(os.path.join(OUTPUT_DIR,'document-switch','export-close.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),view=str(p.Views[0].Id),detailsOpen=True),f,indent=2)
doc.Modified=False
assert Rhino.RhinoApp.RunScript('_-New _None',False)
