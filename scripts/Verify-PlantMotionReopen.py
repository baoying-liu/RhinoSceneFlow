import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantGroups,PlantEditing
from System.Reflection import BindingFlags
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plant-edit0173');record=json.load(open(os.path.join(folder,'saved.json')));assert doc.Path==record['path']
f=BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic;root=System.Guid('73fb8208-d869-4935-bb7e-23a6e81e4641')
rows={r.Id:[r.Position.X,r.Position.Y,r.Position.Z,r.Scale,r.Mirror] for r in clr.GetClrType(PlantGroups).GetMethod('Rows',f).Invoke(None,System.Array[System.Object]([doc.Objects.FindId(root)]))};assert rows==record['rows']
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
state=api('plant_group_state',groupId=str(root));assert not state['busy'] and state['error'] is None,state
api('plant_edit_enter',groupId=str(root),individualId=record['changed'])
clr.GetClrType(PlantEditing).GetMethod('BeginPreview',f).Invoke(None,System.Array[System.Object]([doc,doc.Views.ActiveView.ActiveViewport,False]));assert api('plant_edit_status')['dragging']
assert not doc.Modified
json.dump(dict(pid=EXPECTED_PID,immediatePoseSavedAndReopened=True,layoutIdentical=True,newFromActivePreview=True),open(os.path.join(folder,'reopened.json'),'w'),indent=2)
assert Rhino.RhinoApp.RunScript('_-New _None',False)
