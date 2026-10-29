"""B-only shared-library UI fixture. Uses a new private test library and actual PNG."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'shared-library0133');os.makedirs(folder,exist_ok=True)
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.13.3'
original=api('material_library')['directory'];root=os.path.join(folder,'library-'+str(EXPECTED_PID));api('material_configure',directory=root)
image=os.path.join(root,'base.png');os.makedirs(root,exist_ok=True)
b=System.Drawing.Bitmap(64,64);g=System.Drawing.Graphics.FromImage(b);g.Clear(System.Drawing.Color.SteelBlue);g.Dispose();b.Save(image,System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
a=api('material_import',asset=dict(name='Shared',category='Shared',tags=['shared'],widthMeters=1,heightMeters=1),files=dict(baseColor=image))
with open(os.path.join(root,'seed.id'),'w') as f:f.write(a['id'])
with open(os.path.join(root,'start'),'w') as f:f.write('go')
api('material_workspace_group');api('material_tool_select',page='library',assetId=a['id'])
state=api('material_workspace_status');panel=Rhino.UI.Panels.GetPanel(System.Guid(state['pages'][1]['panelId']))
tool=panel.GetType().GetProperty('Tool',BindingFlags.Instance|BindingFlags.NonPublic).GetValue(panel)
field=lambda o,n:o.GetType().GetField(n,BindingFlags.Instance|BindingFlags.NonPublic).GetValue(o)
shelf=field(tool,'shelf');field(shelf,'name').Text='Unsaved local draft'
report=dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),originalLibrary=original,library=root,asset=a)
with open(os.path.join(folder,'setup.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,library=root,asset=a['id'],initialCount=1)))
