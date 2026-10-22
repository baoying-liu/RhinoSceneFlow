"""Request cancellation through the real Eto cancel button while the worker runs."""
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
p.SelectNamedView(entry.Id);field('width').Value=2048;field('height').Value=1047
out=os.path.join(OUTPUT_DIR,'panel','cancel-'+str(System.Guid.NewGuid()).split('-')[0]);field('folder').Text=out
app=System.AppDomain.CurrentDomain;app.SetData('SceneFlowCancelDirectory',out)
app.SetData('SceneFlowPreviousDirectory',SceneFlowPlugin.Instance.ExportDirectory)
task=p.StartExport();app.SetData('SceneFlowCancelTask',task)
timer=UITimer();timer.Interval=.15
def cancel(sender,args):
    timer.Stop()
    button=field('cancel')
    method=button.GetType().GetMethod('PerformClick')
    if method is not None:method.Invoke(button,None);app.SetData('SceneFlowCancelVia','button')
    else:field('cancellation').Cancel();app.SetData('SceneFlowCancelVia','token')
timer.Elapsed+=cancel;timer.Start();app.SetData('SceneFlowCancelTimer',timer)
print(json.dumps(dict(started=True,completed=task.IsCompleted,output=out)))
