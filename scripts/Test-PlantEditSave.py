"""Persist a single-member edit to an owned file; original user model and backup stay untouched."""
import Rhino,System,clr,json,os,traceback
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantGroups
from System.Reflection import BindingFlags
from Eto.Forms import UITimer
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plant-edit0171');root=System.Guid('73fb8208-d869-4935-bb7e-23a6e81e4641');flags=BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
def values():return {r.Id:[r.Position.X,r.Position.Y,r.Position.Z,r.Scale,r.Mirror] for r in clr.GetClrType(PlantGroups).GetMethod('Rows',flags).Invoke(None,System.Array[System.Object]([doc.Objects.FindId(root)]))}
before=values();row=next(iter(before));api('plant_edit_enter',groupId=str(root),individualId=row)
changed=api('plant_edit_transform',transform=[1,0,0,.3,0,1,0,.4,0,0,1,0,0,0,0,1])['individualId']
def queue():
 timer=UITimer();timer.Interval=.3;started=System.DateTime.UtcNow
 def tick(sender,args):
  try:
   assert (System.DateTime.UtcNow-started).TotalSeconds<30
   if Rhino.RhinoApp.InCommand>0 or api('plant_group_state',groupId=str(root))['busy']:return
   timer.Stop();current=values();assert all(current[k]==v for k,v in before.items() if k!=row)
   path=os.path.join(os.environ['LOCALAPPDATA'],'RhinoSceneFlow','Demos','HillsideRetreat','SceneFlow-Hillside-PlantEdit-Regression.3dm')
   options=Rhino.FileIO.FileWriteOptions();options.UpdateDocumentPath=True;options.SuppressDialogBoxes=True;options.IncludeRenderMeshes=True;options.IncludePreviewImage=True
   assert doc.WriteFile(path,options),'Native 3dm save failed'
   assert not api('plant_edit_status')['isolated'],'Save must finish editing'
   assert not doc.Objects.FindId(root).IsLocked
   assert not any(o.Attributes.GetUserString('RhinoSceneFlow.PlantEdit.Lock.v1') for o in doc.Objects)
   json.dump(dict(pid=EXPECTED_PID,path=path,rows=current,changed=changed,saveFinishedIsolation=True),open(os.path.join(folder,'saved.json'),'w'),indent=2)
  except Exception:
   timer.Stop();json.dump(dict(error=traceback.format_exc()),open(os.path.join(folder,'saved.json'),'w'),indent=2)
 timer.Elapsed+=tick;System.AppDomain.CurrentDomain.SetData('SceneFlowPlantEditSaveTest',timer);timer.Start()
queue();print('Native save regression queued')
