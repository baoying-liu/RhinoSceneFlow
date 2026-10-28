import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,ExportPanelController
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'workspace013');p=ExportPanelController.Find(doc.RuntimeSerialNumber)
task=System.AppDomain.CurrentDomain.GetData('Workspace013ExportTask');assert task.IsCompleted and not task.IsFaulted
report=p.LastReport;assert report is not None and not report.Cancelled and all(f.Ok for f in report.Files),p.GetState()
v=doc.Views.ActiveView.ActiveViewport;before=json.loads(System.AppDomain.CurrentDomain.GetData('Workspace013ExportBefore'));assert before==[doc.Objects.Count,doc.Modified,str(v.CameraLocation),int(doc.RenderSettings.Sun.Hash)]
result=dict(pid=EXPECTED_PID,paths=[f.Path for f in report.Files],documentStatePreserved=True)
with open(os.path.join(folder,'export-verified.json'),'w') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
# Leave real controls populated while testing graceful native container teardown.
print(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='material_shelf_open',document=int(doc.RuntimeSerialNumber),visible=True))))
# Never overwrite an opened/locked fixture; SuppressDialogBoxes does not suppress
# Rhino's read-only lock warning. Save this final snapshot to a new owned path.
model=os.path.join(folder,'SceneFlow-Workspace013-ready-'+str(System.Guid.NewGuid())[:8]+'.3dm')
opts=Rhino.FileIO.FileWriteOptions();opts.SuppressDialogBoxes=True;opts.UpdateDocumentPath=True;assert doc.WriteFile(model,opts);doc.Modified=False
with open(os.path.join(folder,'saved-model.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,path=model),f,indent=2)
