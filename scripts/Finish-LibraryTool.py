"""Verify fresh live target and capture the separate library native Eto content."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin');clr.AddReference('PresentationCore');clr.AddReference('PresentationFramework');clr.AddReference('WindowsBase')
from RhinoSceneFlow.Plugin import McpApi
from System.Windows import Size,Rect
from System.Windows.Media import PixelFormats
from System.Windows.Media.Imaging import RenderTargetBitmap,PngBitmapEncoder,BitmapFrame
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'library0131');fixture=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert not api('material_panel_status')['busy']
first=api('material_inspect',objects=fixture['objects'][:1]);second=api('material_inspect',objects=fixture['objects'][1:])
assert first==json.load(open(os.path.join(folder,'first.json')))
assert fixture['assets'][1] in json.dumps(second),second
assert all(v['status']['valid'] for v in api('material_uv_status',objects=fixture['objects']))
state=api('material_shelf_open');assert state['page']=='library' and state['chatKit'] is None
workspace=api('material_workspace_status');panel=Rhino.UI.Panels.GetPanel(System.Guid(workspace['pages'][1]['panelId']))
root=panel.ControlObject;root.UpdateLayout();w=max(380,int(root.ActualWidth));h=max(850,int(root.ActualHeight))
root.Measure(Size(w,h));root.Arrange(Rect(0,0,w,h));root.UpdateLayout()
tool=panel.GetType().GetProperty('Tool',BindingFlags.Instance|BindingFlags.NonPublic).GetValue(panel)
shelf=tool.GetType().GetField('shelf',BindingFlags.Instance|BindingFlags.NonPublic).GetValue(tool)
grid=shelf.GetType().GetField('list',BindingFlags.Instance|BindingFlags.NonPublic).GetValue(shelf)
assert grid.ControlObject.ActualHeight>100,grid.ControlObject.ActualHeight
bitmap=RenderTargetBitmap(int(w*1.5),int(h*1.5),144,144,PixelFormats.Pbgra32);bitmap.Render(root)
encoder=PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(bitmap));stream=System.IO.FileStream(os.path.join(folder,'library.png'),System.IO.FileMode.Create)
try:encoder.Save(stream)
finally:stream.Dispose()
doc.Objects.UnselectAll()
for oid in fixture['originalSelection']:
 obj=doc.Objects.FindId(System.Guid(oid))
 if obj:obj.Select(True)
report=dict(pid=EXPECTED_PID,firstUnchanged=True,secondLiveTarget=True,automaticUvValid=True,listHeight=grid.ControlObject.ActualHeight,workspace=workspace)
with open(os.path.join(folder,'verified.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(firstUnchanged=True,secondLiveTarget=True,automaticUvValid=True,capture=os.path.join(folder,'library.png'))))
