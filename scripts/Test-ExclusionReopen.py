"""Reopen only the owned B fixture, after the Platform command returns."""
import Rhino,System,clr,json,os,traceback
from Eto.Forms import UITimer
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'exclusions0232');s=json.load(open(os.path.join(folder,'setup.json')))
assert Rhino.RhinoDoc.ActiveDoc.Path==s['model'] and not Rhino.RhinoDoc.ActiveDoc.Modified
output=os.path.join(folder,'reopen-verified.json')
if os.path.exists(output):os.remove(output)
timer=UITimer();timer.Interval=.3;started=System.DateTime.UtcNow
def tick(sender,args):
    try:
        assert (System.DateTime.UtcNow-started).TotalSeconds<45
        if Rhino.RhinoApp.InCommand>0:return
        timer.Stop()
        assert Rhino.RhinoApp.RunScript('_-Open "'+s['model']+'" _Enter',False)
        fresh=Rhino.RhinoDoc.ActiveDoc
        def api(op,**kw):
            r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(fresh.RuntimeSerialNumber),**kw))));assert r['ok'],r;return r['result']
        group=api('plant_group_state',groupId=s['group'])
        assert group['spec']['exclusionObjects']==[s['obstacle']] and group['spec']['exclusionMode']=='geometry'
        views=api('workbench_settings')['views'];view=next(v for v in views if v['id']==s['view'])
        assert (view['width'],view['height'])==(256,192),'Reopen lost sidecar output settings'
        assert fresh.Path==s['model'] and not fresh.Modified
        json.dump(dict(pid=EXPECTED_PID,reopened=True,trimAndReferencesPersisted=True,width=view['width'],height=view['height'],modelUnmodified=True,document=int(fresh.RuntimeSerialNumber)),open(output,'w'),indent=2)
    except Exception:
        timer.Stop();json.dump(dict(error=traceback.format_exc()),open(output,'w'),indent=2)
timer.Elapsed+=tick;System.AppDomain.CurrentDomain.SetData('SceneFlowExclusionReopen0232',timer);timer.Start()
print('Owned fixture reopen queued')
