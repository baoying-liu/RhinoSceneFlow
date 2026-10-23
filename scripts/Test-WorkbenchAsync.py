"""B-only real two-view UI export, or cancellation; return without blocking dispatcher."""
import clr,Rhino,System,os,json
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import ExportPanelController,SceneFlowPlugin
from Eto.Forms import UITimer
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;p=ExportPanelController.Find(doc.RuntimeSerialNumber);assert p is not None
app=System.AppDomain.CurrentDomain
cancel_mode=bool(app.GetData('WorkbenchTestCancel'))
def field(name):return p.GetType().GetField(name,BindingFlags.Instance|BindingFlags.NonPublic).GetValue(p)
app.SetData('WorkbenchSavedRows',System.Array[System.Object]([r.Copy() for r in p.Views]))
app.SetData('WorkbenchSavedDirectory',SceneFlowPlugin.Instance.ExportDirectory)
app.SetData('WorkbenchBefore',json.dumps([doc.Modified,str(doc.Views.ActiveView.ActiveViewport.CameraLocation),str(doc.Views.ActiveView.ActiveViewport.Size),int(doc.RenderSettings.Sun.Hash),len(list(doc.Views.GetViewList(False,True)))]))
for i,r in enumerate(list(p.Views)):
 copy=r.Copy();copy.Included=i<(1 if cancel_mode else 2)
 copy.Width=4096 if cancel_mode else 320;copy.Height=2048 if cancel_mode else 200
 p.SetView(copy)
out=os.path.join(OUTPUT_DIR,'workbench',('cancel-' if cancel_mode else 'async-')+str(System.Guid.NewGuid())[:8]);field('folder').Text=out
app.SetData('WorkbenchOut',out);app.SetData('WorkbenchTicks',0)
timer=UITimer();timer.Interval=.05
def tick(sender,args):
 if p.IsExporting:app.SetData('WorkbenchTicks',int(app.GetData('WorkbenchTicks'))+1)
timer.Elapsed+=tick;timer.Start();app.SetData('WorkbenchTimer',timer)
task=p.StartExport();app.SetData('WorkbenchTask',task)
if cancel_mode:
 cancel=UITimer();cancel.Interval=.15
 def stop(sender,args):
  cancel.Stop();field('cancel').GetType().GetMethod('PerformClick').Invoke(field('cancel'),None)
 cancel.Elapsed+=stop;cancel.Start();app.SetData('WorkbenchCancelTimer',cancel)
print(json.dumps(dict(started=True,cancel=cancel_mode,completed=task.IsCompleted,output=out)))
