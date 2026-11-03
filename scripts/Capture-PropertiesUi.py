import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin');clr.AddReference('PresentationCore');clr.AddReference('PresentationFramework');clr.AddReference('WindowsBase')
from RhinoSceneFlow.Plugin import McpApi
from System.Windows import Size,Rect
from System.Windows.Media import PixelFormats
from System.Windows.Media.Imaging import RenderTargetBitmap,PngBitmapEncoder,BitmapFrame
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
folder=os.path.join(OUTPUT_DIR,'properties017');doc=__rhino_doc__
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
for page,index in [('plantsList',5),('properties',6)]:
 state=api('material_workspace_open',page=page);panel=Rhino.UI.Panels.GetPanel(System.Guid(state['pages'][index]['panelId']));native=panel.ControlObject
 native.Measure(Size(440,850));native.Arrange(Rect(0,0,440,850));native.UpdateLayout();bitmap=RenderTargetBitmap(440,850,96,96,PixelFormats.Pbgra32);bitmap.Render(native)
 encoder=PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(bitmap));stream=System.IO.FileStream(os.path.join(folder,page+'.png'),System.IO.FileMode.Create)
 try:encoder.Save(stream)
 finally:stream.Dispose()
with open(os.path.join(folder,'workspace-final.json'),'w') as f:json.dump(api('material_workspace_status'),f,indent=2)
print('WPF panel layout captures saved (native viewport excluded)')
