"""Time immediate single-member commits on the backed-up B model; cancel all test edits."""
import Rhino,System,clr,json,os,statistics
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantGroups
from System.Reflection import BindingFlags
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plant-edit0173');record=json.load(open(os.path.join(folder,'backup.json')));assert doc.Path==record['backup']
root=System.Guid('73fb8208-d869-4935-bb7e-23a6e81e4641');f=BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic;pg=clr.GetClrType(PlantGroups);key=pg.GetField('Key',f).GetRawConstantValue()
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
def values():return {r.Id:[r.Position.X,r.Position.Y,r.Position.Z,r.Scale,r.Mirror] for r in pg.GetMethod('Rows',f).Invoke(None,System.Array[System.Object]([doc.Objects.FindId(root)]))}
before=values();original=doc.Objects.FindId(root).Attributes.GetUserString(key);chosen=next(iter(before));times=[]
api('plant_edit_enter',groupId=str(root),individualId=chosen)
try:
 for i in range(12):
  sw=System.Diagnostics.Stopwatch.StartNew();changed=api('plant_edit_transform',transform=[1,0,0,.05,0,1,0,-.02,0,0,1,0,0,0,0,1])['individualId'];times.append(sw.Elapsed.TotalMilliseconds)
  state=api('plant_group_state',groupId=str(root));assert not state['busy'] and state['error'] is None,state
  now=values();assert len(now)==len(before)
  assert all(now[k]==v for k,v in before.items() if k!=chosen),'Other plants moved'
  assert api('plant_edit_status')['gumball'],'Gumball should remain immediately usable'
 api('plant_edit_transform',transform=[1,0,0,.4,0,1,0,0,0,0,1,0,0,0,0,1],copy=True)
 assert len(values())==len(before)+1 and not api('plant_group_state',groupId=str(root))['busy']
 json.dump(dict(pid=EXPECTED_PID,commits=len(times),medianMs=statistics.median(times),maximumMs=max(times),samplesMs=times,noPendingLayout=True,otherMembersUnchanged=True,copyImmediate=True,trees=len(before)),open(os.path.join(folder,'commit.json'),'w'),indent=2)
 print(json.dumps(dict(medianMs=statistics.median(times),maximumMs=max(times))))
finally:
 api('plant_edit_cancel');assert doc.Objects.FindId(root).Attributes.GetUserString(key)==original
