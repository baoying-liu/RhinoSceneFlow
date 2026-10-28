"""Capture actual dock content, select/apply to live targets and send a real ChatKit search turn."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin');clr.AddReference('PresentationCore');clr.AddReference('PresentationFramework');clr.AddReference('WindowsBase')
from RhinoSceneFlow.Plugin import McpApi
from System.Windows import Size,Rect
from System.Windows.Media import PixelFormats
from System.Windows.Media.Imaging import RenderTargetBitmap,PngBitmapEncoder,BitmapFrame
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'workspace013');fixture=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
def field(o,n):return o.GetType().GetField(n,BindingFlags.Instance|BindingFlags.NonPublic).GetValue(o)
def prop(o,n):return o.GetType().GetProperty(n,BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public).GetValue(o)
def capture(panel,path):
 root=panel.ControlObject;root.Measure(Size(380,900));desired=[root.DesiredSize.Width,root.DesiredSize.Height];root.Arrange(Rect(0,0,380,900));root.UpdateLayout()
 bitmap=RenderTargetBitmap(380,900,96,96,PixelFormats.Pbgra32);bitmap.Render(root);encoder=PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(bitmap))
 stream=System.IO.FileStream(path,System.IO.FileMode.Create)
 try:encoder.Save(stream)
 finally:stream.Dispose()
 return desired
state=api('material_workspace_status');captures={}
for page in ['export','uv','planting','materials']:
 api('material_workspace_open',page=page);state=api('material_workspace_status');panel=Rhino.UI.Panels.GetPanel(System.Guid(state['pages'][['materials','uv','planting','export'].index(page)]['panelId']))
 assert panel is not None
 captures[page]=capture(panel,os.path.join(folder,page+'-dock.png'))
 if page=='materials':tool=prop(panel,'Tool')
shelf=field(tool,'shelf');shelf.Select(System.Guid(fixture['assets'][0]));shelf.Select(System.Guid(fixture['assets'][1]));shelf.Select(System.Guid(fixture['assets'][0]))
api('material_shelf_open',visible=True);captures['library']=capture(panel,os.path.join(folder,'library-dock.png'));api('material_shelf_open',visible=False)
api('material_tool_select',assetId=fixture['assets'][0]);api('material_tool_apply')
chat=field(tool,'chat');browser=field(chat,'Browser');assert browser.CoreWebView2 is not None
task=browser.ExecuteScriptAsync("window.chat.sendUserMessage({text:'生成一种浅灰天然石灰岩，无接缝、哑光、均匀细腻。优先使用已有的合适材质。'})")
report=dict(pid=EXPECTED_PID,captures=captures,apply=api('material_quick_status'),chatSend='submitted',nativeViews=len(doc.Views.GetViewList(True,True)))
with open(os.path.join(folder,'check.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
