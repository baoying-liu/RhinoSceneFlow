"""Real Rhino commands after Platform completion; uses only the owned backup fixture."""
import Rhino,System,clr,json,os,traceback
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantGroups
from System.Reflection import BindingFlags
from Eto.Forms import UITimer
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plant-edit0171');record=json.load(open(os.path.join(folder,'backup.json')));assert doc.Path==record['backup']
root=System.Guid('73fb8208-d869-4935-bb7e-23a6e81e4641');flags=BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic;key=clr.GetClrType(PlantGroups).GetField('Key',flags).GetRawConstantValue()
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
before=doc.Objects.FindId(root).Attributes.GetUserString(key);row=list(clr.GetClrType(PlantGroups).GetMethod('Rows',flags).Invoke(None,System.Array[System.Object]([doc.Objects.FindId(root)])))[0].Id
prior=int(doc.CurrentUndoRecordSerialNumber)
if prior:assert doc.EndUndoRecord(prior)
def queue():
 timer=UITimer();timer.Interval=.3;phase=0;started=System.DateTime.UtcNow;after=None
 def tick(sender,args):
  nonlocal phase,after
  try:
   assert (System.DateTime.UtcNow-started).TotalSeconds<45
   if Rhino.RhinoApp.InCommand>0 or api('plant_group_state',groupId=str(root))['busy']:return
   if phase==0:
    # Emulate an Eto/Gumball action outside the Platform command's own undo scope.
    prior=int(doc.CurrentUndoRecordSerialNumber)
    if prior:assert doc.EndUndoRecord(prior)
    api('plant_edit_enter',groupId=str(root),individualId=row)
    api('plant_edit_transform',transform=[1,0,0,.15,0,1,0,.12,0,0,1,0,0,0,0,1])
    after=doc.Objects.FindId(root).Attributes.GetUserString(key);assert after!=before;phase=1
   elif phase==1:
    assert Rhino.RhinoApp.RunScript('_Undo',False);phase=2
   elif phase==2:
    assert doc.Objects.FindId(root).Attributes.GetUserString(key)==before,'Undo spec mismatch'
    assert doc.Objects.FindId(root).IsLocked,'Undo escaped isolation'
    assert Rhino.RhinoApp.RunScript('_Redo',False);phase=3
   elif phase==3:
    assert doc.Objects.FindId(root).Attributes.GetUserString(key)==after,'Redo spec mismatch'
    api('plant_edit_exit');assert not doc.Objects.FindId(root).IsLocked
    assert Rhino.RhinoApp.RunScript('_Undo',False);phase=4
   else:
    assert doc.Objects.FindId(root).Attributes.GetUserString(key)==before
    assert not doc.Objects.FindId(root).IsLocked,'Undo after finish left root locked'
    assert not any(o.Attributes.GetUserString('RhinoSceneFlow.PlantEdit.Lock.v1') for o in doc.Objects)
    timer.Stop();json.dump(dict(pid=EXPECTED_PID,nativeUndoRedo=True,isolatedUndoProtected=True,postExitUndoRepaired=True),open(os.path.join(folder,'undo.json'),'w'),indent=2)
  except Exception:
   timer.Stop();json.dump(dict(pid=EXPECTED_PID,error=traceback.format_exc(),phase=phase),open(os.path.join(folder,'undo.json'),'w'),indent=2)
 timer.Elapsed+=tick;System.AppDomain.CurrentDomain.SetData('SceneFlowPlantEditUndoTest',timer);timer.Start()
queue();print('Native isolated Undo/Redo queued')
