import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin');clr.AddReference('Eto')
from RhinoSceneFlow.Plugin import McpApi
from Eto.Forms import DataObject,DragEventArgs,DragEffects,Keys,MouseButtons,MouseEventArgs
from Eto.Drawing import PointF
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;assert doc.Objects.Count==0 and not doc.Modified
folder=os.path.join(OUTPUT_DIR,'plants0161');os.makedirs(folder,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.16.1'
original=api('material_library')['directory'];fixture=json.load(open(os.path.join(OUTPUT_DIR,'plants015','setup.json')))['library']
api('material_configure',directory=fixture);assets=api('plant_library')['assets'];assert len(assets)>=3
api('plant_ui_settings',settings=dict(language='zh',libraryView='tiles',compositionView='tiles'))
api('material_workspace_open',page='planting');state=api('material_workspace_status');panel=Rhino.UI.Panels.GetPanel(System.Guid(state['pages'][3]['panelId']));flags=BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic;tool=panel.GetType().GetProperty('Tool',flags).GetValue(panel)
def field(o,key):return o.GetType().GetField(key,flags).GetValue(o)
tool.GetType().GetMethod('NewDraft',flags).Invoke(tool,None)
source=field(field(tool,'list'),'canvas');palette=field(tool,'palette')
for a in assets[:3]:
 data=DataObject();data.Text='SceneFlowPlant:'+a['id'];event=DragEventArgs(source,data,DragEffects.Copy,PointF(10,10),Keys(0),MouseButtons.Primary,None)
 palette.GetType().GetMethod('OnDragDrop',flags).Invoke(palette,System.Array[System.Object]([event]))
details=api('material_workspace_status')['tools']['planting']['details'];assert len(details['palette'])==3
for entry in details['palette']:assert abs(entry['spacingMeters']-next(a for a in assets if a['id']==entry['asset'])['plant']['spacingMeters'])<1e-9
field(tool,'spacing').Value=6
record=dict(pid=EXPECTED_PID,originalLibrary=original,fixture=fixture,before=assets,document=int(doc.RuntimeSerialNumber),lastAsset=assets[2]['id'],defaultSpacingVerified=True)
with open(os.path.join(folder,'setup.json'),'w') as f:json.dump(record,f,indent=2)
print('Three plants dropped through native Eto events; AI spacing defaults populated; manual spacing changed to 6')
