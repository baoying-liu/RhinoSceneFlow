"""B-only, backed-up Hillside fixture. No OS mouse input; tests the native list event and shared Gumball commit path."""
import Rhino,System,clr,json,os,traceback
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantEditing,PlantGroups
from System.Reflection import BindingFlags
from Eto.Forms import UITimer,GridCellMouseEventArgs,MouseButtons,Keys
from Eto.Drawing import PointF,SizeF
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;flags=BindingFlags.Static|BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic
folder=os.path.join(OUTPUT_DIR,'plant-edit0171');receipt=json.load(open(os.path.join(folder,'backup.json')))
assert doc.Path==receipt['backup'],'Must use the saved user-state copy'
root=System.Guid('73fb8208-d869-4935-bb7e-23a6e81e4641');pg=clr.GetClrType(PlantGroups)
key=pg.GetField('Key',flags).GetRawConstantValue();lock='RhinoSceneFlow.PlantEdit.Lock.v1'
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
def rows():
 return list(pg.GetMethod('Rows',flags).Invoke(None,System.Array[System.Object]([doc.Objects.FindId(root)])))
def values():return {r.Id:[r.Position.X,r.Position.Y,r.Position.Z,r.Scale,r.Mirror] for r in rows()}
def objects():
 settings=Rhino.DocObjects.ObjectEnumeratorSettings();settings.NormalObjects=True;settings.LockedObjects=True;settings.HiddenObjects=True
 return list(doc.Objects.GetObjectList(settings))
baseline=doc.Objects.FindId(root).Attributes.GetUserString(key);before=values();modes={str(o.Id):str(o.Attributes.Mode) for o in objects()};count=len(objects())
json.dump(dict(spec=baseline,rows=before,modes=modes,count=count),open(os.path.join(folder,'isolation-baseline.json'),'w'),indent=2)
api('plant_list_select',groups=[str(root)]);ws=api('material_workspace_status');panel=Rhino.UI.Panels.GetPanel(System.Guid(ws['pages'][5]['panelId']));tool=panel.GetType().GetProperty('Tool',flags).GetValue(panel);grid=tool.GetType().GetField('list',flags).GetValue(tool)
tool.GetType().GetMethod('Refresh',flags).Invoke(tool,None)
item=list(grid.DataStore)[0]
event=GridCellMouseEventArgs(grid.Columns[0],0,0,item,MouseButtons.Primary,System.Enum.ToObject(clr.GetClrType(Keys),0),PointF(4,4),None,0.0)
grid.GetType().GetMethod('OnCellDoubleClick',flags).Invoke(grid,System.Array[System.Object]([event]))
assert api('plant_edit_status')['isolated'],'Actual Eto double-click did not enter'
assert doc.Objects.FindId(root).IsLocked
assert not list(doc.Objects.GetSelectedObjects(False,False))
for o in objects():
 if modes[str(o.Id)]=='Normal':assert o.IsLocked and not doc.Objects.Select(o.Id),'Outside object selectable'
row=rows()[0];api('plant_edit_enter',groupId=str(root),individualId=row.Id)
assert api('plant_edit_status')['gumball']
move=[1,0,0,.75,0,1,0,-.5,0,0,1,0,0,0,0,1]
changed=api('plant_edit_transform',transform=move)['individualId']
def queue(changed):
 timer=UITimer();timer.Interval=.25;phase=0;started=System.DateTime.UtcNow;result=dict(pid=EXPECTED_PID,listDoubleClick=True,isolationLocks=True,baseline=count)
 def tick(sender,args):
  nonlocal phase,changed
  try:
   assert (System.DateTime.UtcNow-started).TotalSeconds<45,'Timed out'
   state=api('plant_group_state',groupId=str(root))
   if state['busy']:return
   assert not state['error'],state
   if phase==0:
    # Display handles refresh on their own UI timer after the layout commit.
    if not api('plant_edit_status')['gumball']:return
    current=values();assert len(current)==len(before)
    assert changed in current and changed!=row.Id
    assert all(current[k]==v for k,v in before.items() if k!=row.Id),'Moving one tree rearranged other trees'
    assert len(objects())==count
    result['moveOnlyOne']=True;result['gumball']=api('plant_edit_status')['gumball'];assert result['gumball']
    changed=api('plant_edit_transform',transform=move,copy=True)['individualId'];phase=1
   elif phase==1:
    assert len(values())==len(before)+1 and len(objects())==count,'Copy duplicated the group or lost members'
    result['copyOnlyOne']=True
    api('plant_edit_cancel');assert doc.Objects.FindId(root).Attributes.GetUserString(key)==baseline
    assert {str(o.Id):str(o.Attributes.Mode) for o in objects()}==modes
    assert not any(o.Attributes.GetUserString(lock) for o in objects());phase=2
   else:
    assert values()==before,'Cancel did not restore layout'
    result['cancelRestoredExactSpecAndLayout']=True;result['locksRestored']=True
    timer.Stop();json.dump(result,open(os.path.join(folder,'isolation.json'),'w'),indent=2)
  except Exception:
   timer.Stop();result['error']=traceback.format_exc();json.dump(result,open(os.path.join(folder,'isolation.json'),'w'),indent=2)
 timer.Elapsed+=tick;System.AppDomain.CurrentDomain.SetData('SceneFlowIsolationTest',timer);timer.Start()
queue(changed);print('Isolation test queued; no OS mouse input')






