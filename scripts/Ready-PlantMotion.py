"""Keep the user's dirty pre-test model in a new named copy; never overwrite the original."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,PlantGroups
from System.Reflection import BindingFlags
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plant-edit0173');record=json.load(open(os.path.join(folder,'backup.json')));assert doc.Path==record['backup'] and not doc.Modified
root=System.Guid('73fb8208-d869-4935-bb7e-23a6e81e4641');f=BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic;pg=clr.GetClrType(PlantGroups);key=pg.GetField('Key',f).GetRawConstantValue()
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
state=api('plant_group_state',groupId=str(root));assert not state['busy'] and state['error'] is None
rows={r.Id:[r.Position.X,r.Position.Y,r.Position.Z,r.Scale,r.Mirror] for r in pg.GetMethod('Rows',f).Invoke(None,System.Array[System.Object]([doc.Objects.FindId(root)]))}
path=os.path.join(os.path.dirname(record['original']),'SceneFlow-Hillside-Retreat-PlantMotion-Fixed.3dm')
options=Rhino.FileIO.FileWriteOptions();options.UpdateDocumentPath=True;options.SuppressDialogBoxes=True;options.IncludeRenderMeshes=True;options.IncludePreviewImage=True
assert doc.WriteFile(path,options) and not doc.Modified
for view in record['views']:api('configure_view',viewId=view['id'],settings=view)
api('material_workspace_open',page='properties');api('plant_list_select',groups=[str(root)])
ws=api('material_workspace_status');assert all(v['error'] is None for v in ws['tools'].values())
json.dump(dict(pid=EXPECTED_PID,version=api('describe')['version'],path=path,original=record['original'],backup=record['backup'],userUnsavedChangesPreserved=record['modified'],rows=rows,spec=doc.Objects.FindId(root).Attributes.GetUserString(key),modified=doc.Modified,editing=api('plant_edit_status')),open(os.path.join(folder,'ready.json'),'w'),indent=2)
print(json.dumps(dict(path=path,trees=len(rows),modified=doc.Modified)))
