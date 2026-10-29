import Rhino,System,clr,json,os
clr.AddReference('RhinoSceneFlow.Plugin');clr.AddReference('PresentationCore');clr.AddReference('PresentationFramework');clr.AddReference('WindowsBase')
from RhinoSceneFlow.Plugin import McpApi
from System.Windows import Size,Rect
from System.Windows.Media import PixelFormats
from System.Windows.Media.Imaging import RenderTargetBitmap,PngBitmapEncoder,BitmapFrame
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;assert doc.Objects.Count==0 and not doc.Modified
folder=os.path.join(OUTPUT_DIR,'plants015');setup=json.load(open(os.path.join(folder,'setup.json')));ai=json.load(open(os.path.join(folder,'ai-verified.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.15.0';api('material_configure',directory=setup['library']);state=api('material_workspace_group');assert all(t['error'] is None for t in state['tools'].values())
api('plant_select',assetId=ai['asset']['id']);panel=Rhino.UI.Panels.GetPanel(System.Guid(state['pages'][3]['panelId']));root=panel.ControlObject;root.Measure(Size(420,950));root.Arrange(Rect(0,0,420,950));root.UpdateLayout()
b=RenderTargetBitmap(630,1425,144,144,PixelFormats.Pbgra32);b.Render(root);encoder=PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(b));stream=System.IO.FileStream(os.path.join(folder,'plant-tool-ready.png'),System.IO.FileMode.Create)
try:encoder.Save(stream)
finally:stream.Dispose()
job=api('material_chat_start',conversation='生成美国红枫 Acer rubrum 夏季绿叶透明植物，树形与参考图相同，优先复用已有的真实植物素材。',referenceImages=[ai['job']['imagePath']],reuseSimilar=True)
with open(os.path.join(folder,'ready-start.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),job=job['id']),f,indent=2)
print('Fixed footer captured; actual candidate-image reuse verification running')
