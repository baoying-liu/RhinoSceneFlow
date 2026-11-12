"""Native B fixture only: queue Undo/Redo after Platform's command has finished."""
import Rhino,System,clr,json,os,traceback
from Eto.Forms import UITimer
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=Rhino.RhinoDoc.ActiveDoc;folder=os.path.join(OUTPUT_DIR,'exclusions0232')
record=json.load(open(os.path.join(folder,'setup.json')))
assert doc.Path==record['model'],'Only the owned test model may be modified'
def api(op,**kw):
    r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
    assert r['ok'],r
    return r['result']
output=os.path.join(folder,'undo-verified.json')
if os.path.exists(output):os.remove(output)
timer=UITimer();timer.Interval=.25;phase=0;started=System.DateTime.UtcNow
def tick(sender,args):
    global phase
    try:
        assert (System.DateTime.UtcNow-started).TotalSeconds<60,'Undo test timed out'
        if Rhino.RhinoApp.InCommand>0:return
        state=api('plant_group_state',groupId=record['group'])
        if state['busy']:return
        spec=state['spec']
        if phase==0:
            prior=int(doc.CurrentUndoRecordSerialNumber)
            if prior:assert doc.EndUndoRecord(prior)
            if spec['exclusionObjects']!=[record['obstacle']]:
                spec['exclusionObjects']=[record['obstacle']];api('plant_group_update',groupId=record['group'],spec=spec);return
            spec['exclusionObjects']=[];api('plant_group_update',groupId=record['group'],spec=spec);phase=1
        elif phase==1:
            assert spec['exclusionObjects']==[];assert Rhino.RhinoApp.RunScript('_Undo',False);phase=2
        elif phase==2:
            assert spec['exclusionObjects']==[record['obstacle']],'Undo lost exclusion references'
            assert Rhino.RhinoApp.RunScript('_Redo',False);phase=3
        elif phase==3:
            assert spec['exclusionObjects']==[],'Redo did not clear references'
            assert Rhino.RhinoApp.RunScript('_Undo',False);phase=4
        else:
            assert spec['exclusionObjects']==[record['obstacle']]
            opts=Rhino.FileIO.FileWriteOptions();opts.UpdateDocumentPath=True;opts.SuppressDialogBoxes=True;assert doc.WriteFile(record['model'],opts)
            timer.Stop();json.dump(dict(pid=EXPECTED_PID,nativeUndo=True,nativeRedo=True,referencesRestored=True,model=record['model']),open(output,'w'),indent=2)
    except Exception:
        timer.Stop();json.dump(dict(error=traceback.format_exc(),phase=phase),open(output,'w'),indent=2)
timer.Elapsed+=tick;System.AppDomain.CurrentDomain.SetData('SceneFlowExclusionUndo0232',timer);timer.Start()
print('Exclusion Undo/Redo queued outside Platform command')
