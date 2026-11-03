"""Call five times, allowing UI ticks between calls; assert real Eto/native bidirectional events."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
from System.Reflection import BindingFlags
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'properties017');record=json.load(open(os.path.join(folder,'setup.json')));group=System.Guid(record['group'])
path=os.path.join(folder,'selection.json');stage=json.load(open(path))['stage'] if os.path.exists(path) else 0
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
api('material_workspace_open',page='plantsList');flags=BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic
panel=Rhino.UI.Panels.GetPanel(System.Guid(api('material_workspace_status')['pages'][5]['panelId']));tool=panel.GetType().GetProperty('Tool',flags).GetValue(panel);grid=tool.GetType().GetField('list',flags).GetValue(tool)
if stage==0:
 api('plant_list_select',groups=[str(group)]);grid.UnselectAll()
elif stage==1:
 assert doc.Objects.FindId(group).IsSelected(False)==0,'List deselection did not reach viewport'
 grid.SelectRow(0)
elif stage==2:
 assert doc.Objects.FindId(group).IsSelected(False)>0,'List selection did not reach viewport'
 doc.Objects.UnselectAll()
elif stage==3:
 assert list(grid.SelectedRows)==[],'Native deselection did not reach list'
 doc.Objects.Select(group)
elif stage==4:
 assert list(grid.SelectedRows)==[0],'Native selection did not reach list'
with open(path,'w') as f:json.dump(dict(stage=stage+1,passed=stage>=4,pid=EXPECTED_PID),f)
print('Selection stage '+str(stage)+' passed')
