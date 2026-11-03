"""Call in three UI-separated phases to exercise the actual properties controls and UV queue."""
import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
from System.Reflection import BindingFlags
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'properties017');record=json.load(open(os.path.join(folder,'setup.json')));path=os.path.join(folder,'ui.json');stage=json.load(open(path))['stage'] if os.path.exists(path) else 0
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
state=api('material_workspace_open',page='properties');panel=Rhino.UI.Panels.GetPanel(System.Guid(state['pages'][6]['panelId']));flags=BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;tool=panel.GetType().GetProperty('Tool',flags).GetValue(panel)
def field(name):return tool.GetType().GetField(name,flags).GetValue(tool)
if stage==0:
 doc.Objects.UnselectAll();doc.Objects.Select(System.Guid(record['objects'][0]))
elif stage==1:
 assert field('scope').SelectedKey=='material';field('roughness').Value=.27
 assert field('editRoughness').Checked
 tool.GetType().GetMethod('ApplyMaterial',flags).Invoke(tool,None)
elif stage==2:
 from Rhino.Render import RenderTexture
 for id in record['objects'][:2]:
  obj=doc.Objects.FindId(System.Guid(id));assert abs(obj.GetRenderMaterial(True).ToMaterial(RenderTexture.TextureGeneration.Allow).PhysicallyBased.Roughness-.27)<1e-6
  status=api('material_uv_status',objects=[id]);assert status[0]['status']['valid'],status
 assert not field('actions').GetType().GetProperty('Busy',flags).GetValue(field('actions'))
with open(path,'w') as f:json.dump(dict(stage=stage+1,passed=stage>=2,pid=EXPECTED_PID,status=field('status').Text),f)
print('Properties UI phase '+str(stage)+' passed')
