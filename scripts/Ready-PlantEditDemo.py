"""Restore the user's pre-test group parameters and save a separate demo copy."""
import Rhino,System,clr,json,os,traceback
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantGroups
from System.Reflection import BindingFlags
from Eto.Forms import UITimer
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plant-edit0171');record=json.load(open(os.path.join(folder,'backup.json')));assert doc.Path==record['backup']
baseline=json.load(open(os.path.join(folder,'isolation-baseline.json')));root=System.Guid('73fb8208-d869-4935-bb7e-23a6e81e4641');flags=BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic;key=clr.GetClrType(PlantGroups).GetField('Key',flags).GetRawConstantValue()
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
api('plant_edit_exit');a=doc.Objects.FindId(root).Attributes.Duplicate();a.SetUserString(key,baseline['spec']);assert doc.Objects.ModifyAttributes(root,a,True)
def queue():
 timer=UITimer();timer.Interval=.35;started=System.DateTime.UtcNow
 def tick(sender,args):
  try:
   assert (System.DateTime.UtcNow-started).TotalSeconds<45
   if Rhino.RhinoApp.InCommand>0 or api('plant_group_state',groupId=str(root))['busy']:return
   timer.Stop();rows={r.Id:[r.Position.X,r.Position.Y,r.Position.Z,r.Scale,r.Mirror] for r in clr.GetClrType(PlantGroups).GetMethod('Rows',flags).Invoke(None,System.Array[System.Object]([doc.Objects.FindId(root)]))}
   assert rows==baseline['rows'],'User layout not restored'
   path=os.path.join(os.path.dirname(record['original']),'SceneFlow-Hillside-Retreat-PlantEdit-Fixed.3dm')
   options=Rhino.FileIO.FileWriteOptions();options.UpdateDocumentPath=True;options.SuppressDialogBoxes=True;options.IncludeRenderMeshes=True;options.IncludePreviewImage=True
   assert doc.WriteFile(path,options) and not doc.Modified
   for view in record['views']:api('configure_view',viewId=view['id'],settings=view)
   api('plant_list_select',groups=[str(root)]);api('material_workspace_open',page='properties');api('material_workspace_open',page='plantsList')
   health=api('material_workspace_status');assert all(t['error'] is None for t in health['tools'].values())
   json.dump(dict(pid=EXPECTED_PID,version=api('describe')['version'],path=path,originalPreserved=record['original'],backup=record['backup'],userLayoutRestored=True,trees=len(rows),allToolsHealthy=True,modified=doc.Modified,editing=api('plant_edit_status')),open(os.path.join(folder,'ready.json'),'w'),indent=2)
  except Exception:
   timer.Stop();json.dump(dict(error=traceback.format_exc()),open(os.path.join(folder,'ready.json'),'w'),indent=2)
 timer.Elapsed+=tick;System.AppDomain.CurrentDomain.SetData('SceneFlowPlantEditReady',timer);timer.Start()
queue();print('Restore and save separate test copy queued')
