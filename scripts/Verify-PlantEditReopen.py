import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantGroups
from System.Reflection import BindingFlags
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plant-edit0171');record=json.load(open(os.path.join(folder,'saved.json')));assert doc.Path==record['path']
flags=BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic;root=System.Guid('73fb8208-d869-4935-bb7e-23a6e81e4641')
rows={r.Id:[r.Position.X,r.Position.Y,r.Position.Z,r.Scale,r.Mirror] for r in clr.GetClrType(PlantGroups).GetMethod('Rows',flags).Invoke(None,System.Array[System.Object]([doc.Objects.FindId(root)]))}
assert rows==record['rows'],'Saved/reloaded layout differs'
assert not doc.Objects.FindId(root).IsLocked
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
state=api('plant_group_state',groupId=str(root));assert not state['busy'] and state['error'] is None,state
api('plant_edit_enter',groupId=str(root),individualId=record['changed']);assert api('plant_edit_status')['gumball']
assert not doc.Modified,'Temporary locks should not dirty document'
json.dump(dict(pid=EXPECTED_PID,savedLayoutIdentical=True,singlePlantCustomPersisted=True,temporaryLocksClean=True,newFromActiveIsolation=True),open(os.path.join(folder,'reopened.json'),'w'),indent=2)
assert Rhino.RhinoApp.RunScript('_-New _None',False)
