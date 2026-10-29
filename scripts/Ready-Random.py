import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin');clr.AddReference('PresentationCore');clr.AddReference('PresentationFramework');clr.AddReference('WindowsBase')
from RhinoSceneFlow.Plugin import McpApi
from System.Windows import Size,Rect
from System.Windows.Media import PixelFormats
from System.Windows.Media.Imaging import RenderTargetBitmap,PngBitmapEncoder,BitmapFrame
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'random014');setup=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.14.0'
assert api('material_library')['directory']==setup['originalLibrary']
api('material_configure',directory=setup['library'])
state=api('material_workspace_group');assert all(t['error'] is None for t in state['tools'].values())
api('material_tool_select',assetId=setup['asset']['id']);api('material_shelf_open')
api('material_native_preview',assetId=setup['asset']['id'],path=os.path.join(folder,'native-sphere-final.png'))
panel=Rhino.UI.Panels.GetPanel(System.Guid(state['pages'][1]['panelId']))
tool=panel.GetType().GetProperty('Tool',BindingFlags.Instance|BindingFlags.NonPublic).GetValue(panel)
field=lambda n:tool.GetType().GetField(n,BindingFlags.Instance|BindingFlags.NonPublic).GetValue(tool)
field('randomSettings').Expanded=True
root=panel.ControlObject;root.Measure(Size(420,950));root.Arrange(Rect(0,0,420,950));root.UpdateLayout()
bitmap=RenderTargetBitmap(630,1425,144,144,PixelFormats.Pbgra32);bitmap.Render(root)
encoder=PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(bitmap));stream=System.IO.FileStream(os.path.join(folder,'random-ui-final.png'),System.IO.FileMode.Create)
try:encoder.Save(stream)
finally:stream.Dispose()
api('material_configure',directory=setup['originalLibrary'])
with open(os.path.join(folder,'ready.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,version='0.14.0',allToolsHealthy=True,originalLibraryRestored=True,nativeCachedSphereRendered=True),f,indent=2)
print('Final version, native cached sphere and docked controls verified; original library restored')
