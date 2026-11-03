import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
from Rhino.Render import RenderTexture
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'properties017');record=json.load(open(os.path.join(folder,'setup.json')));id=System.Guid(record['objects'][0])
assert doc.Path==record['model'],'Only the owned regression fixture may close a prior scripted undo record'
prior=int(doc.CurrentUndoRecordSerialNumber)
if prior:assert doc.EndUndoRecord(prior),'Could not finish prior scripted record for isolated undo test'
def value():return doc.Objects.FindId(id).GetRenderMaterial(True).ToMaterial(RenderTexture.TextureGeneration.Allow).PhysicallyBased.Metallic
before=value();after=.23 if abs(before-.81)<1e-6 else .81
r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='selection_material_update',document=int(doc.RuntimeSerialNumber),objects=[str(id)],metallic=after))));assert r['ok'],r
assert abs(value()-after)<1e-6
# Platform run_python is itself a command: Undo must happen after it returns.
from Eto.Forms import UITimer
oldTimer=System.AppDomain.CurrentDomain.GetData('SceneFlowPropertiesUndoTimer')
if oldTimer is not None:oldTimer.Stop();oldTimer.Dispose()
def queue(target,objectId,previous,updated,output,pid):
 localTimer=UITimer();localTimer.Interval=.2;phase=0;started=System.DateTime.UtcNow;events=[]
 def localValue():return target.Objects.FindId(objectId).GetRenderMaterial(True).ToMaterial(RenderTexture.TextureGeneration.Allow).PhysicallyBased.Metallic
 def tick(sender,args):
  nonlocal phase
  try:
   if Rhino.RhinoApp.InCommand>0:
    assert (System.DateTime.UtcNow-started).TotalSeconds<10,'Command did not finish'
    return
   events.append(dict(phase=phase,current=int(target.CurrentUndoRecordSerialNumber),recording=target.UndoRecordingEnabled,undoActive=target.UndoActive,redoActive=target.RedoActive,value=localValue()))
   if phase==0:
    assert Rhino.RhinoApp.RunScript('_Undo',False),'Native Undo command failed'
    assert abs(localValue()-previous)<1e-6,(previous,localValue())
    phase=1
   else:
    assert Rhino.RhinoApp.RunScript('_Redo',False),'Native Redo command failed'
    assert abs(localValue()-updated)<1e-6,(updated,localValue())
    localTimer.Stop()
    with open(output,'w') as f:json.dump(dict(materialUndoRedo=True,pid=pid,before=previous,after=updated,events=events),f)
  except Exception:
   localTimer.Stop()
   import traceback
   with open(output,'w') as f:json.dump(dict(error=traceback.format_exc(),pid=pid,events=events),f)
 localTimer.Elapsed+=tick;System.AppDomain.CurrentDomain.SetData('SceneFlowPropertiesUndoTimer',localTimer);localTimer.Start()
queue(doc,id,before,after,os.path.join(folder,'undo.json'),EXPECTED_PID)
print('Native Undo/Redo queued after Platform command returns')
