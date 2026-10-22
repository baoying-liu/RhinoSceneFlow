"""Start the real panel export; return to Rhino so its UI dispatcher can run."""
import clr,Rhino,System,os,json
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import ExportPanelController,SceneFlowPlugin
from Eto.Forms import UITimer
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;p=ExportPanelController.Find(doc.RuntimeSerialNumber);assert p is not None
def field(name):return p.GetType().GetField(name,BindingFlags.Instance|BindingFlags.NonPublic).GetValue(p)
rows=field('rows');entry=next(r for r in rows if '透视' in r.Name)
for r in rows:r.Included=r.Id==entry.Id
p.SelectNamedView(entry.Id);field('width').Value=352;field('height').Value=224
out=os.path.join(OUTPUT_DIR,'panel','ui-'+str(System.Guid.NewGuid()).split('-')[0])
field('folder').Text=out
app=System.AppDomain.CurrentDomain
app.SetData('SceneFlowPreviousDirectory',SceneFlowPlugin.Instance.ExportDirectory)
app.SetData('SceneFlowUiTicks',0)
app.SetData('SceneFlowUiBusyTicks',0)
timer=UITimer();timer.Interval=.05
def tick(sender,args):
    app.SetData('SceneFlowUiTicks',int(app.GetData('SceneFlowUiTicks'))+1)
    if field('busy'):app.SetData('SceneFlowUiBusyTicks',int(app.GetData('SceneFlowUiBusyTicks'))+1)
timer.Elapsed+=tick;timer.Start();app.SetData('SceneFlowUiTimer',timer)
app.SetData('SceneFlowUiBefore',json.dumps([doc.Modified,str(doc.Views.ActiveView.ActiveViewport.CameraLocation),str(doc.Views.ActiveView.ActiveViewport.Size)]))
task=p.StartExport();app.SetData('SceneFlowUiTask',task)
print(json.dumps(dict(started=True,completed=task.IsCompleted,output=out)))
