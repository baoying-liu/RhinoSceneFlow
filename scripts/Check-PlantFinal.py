import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin');clr.AddReference('PresentationCore');clr.AddReference('PresentationFramework');clr.AddReference('WindowsBase')
from RhinoSceneFlow.Plugin import McpApi,WorkbenchService
from System.Windows import Size,Rect
from System.Windows.Media import PixelFormats
from System.Windows.Media.Imaging import RenderTargetBitmap,PngBitmapEncoder,BitmapFrame
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plants015');setup=json.load(open(os.path.join(folder,'setup.json')));ai=json.load(open(os.path.join(folder,'ai-verified.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert api('describe')['version']=='0.15.0' and len(api('plant_instances')['objects'])==14
state=api('material_workspace_group');assert all(t['error'] is None for t in state['tools'].values()),state
api('plant_select',assetId=ai['asset']['id'])
panel=Rhino.UI.Panels.GetPanel(System.Guid(state['pages'][3]['panelId']));root=panel.ControlObject;root.Measure(Size(420,1000));root.Arrange(Rect(0,0,420,1000));root.UpdateLayout()
bitmap=RenderTargetBitmap(630,1500,144,144,PixelFormats.Pbgra32);bitmap.Render(root);encoder=PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(bitmap));stream=System.IO.FileStream(os.path.join(folder,'plant-tool-final.png'),System.IO.FileMode.Create)
try:encoder.Save(stream)
finally:stream.Dispose()
# Native preview at three orientations: changing global policy never changes object attributes/geometry.
objects=list(doc.Objects);before=[(str(o.Id),int(o.Geometry.DataCRC(0)),o.Attributes.GetUserString('RhinoSceneFlow.Plant.v1')) for o in objects]
row=next(r for r in WorkbenchService.Settings(doc) if str(r.Id)==setup['view']);row.Mode=Rhino.Display.DisplayModeDescription.RenderedId
for mode in ['auto','z','free']:
 api('plant_settings',settings=dict(mode=mode,angle=60,transition=5));b=WorkbenchService.Preview(doc,row,800);b.Save(os.path.join(folder,'native-final-'+mode+'.png'),System.Drawing.Imaging.ImageFormat.Png);b.Dispose()
api('plant_settings',settings=dict(mode='auto',angle=60,transition=5))
after=[(str(o.Id),int(o.Geometry.DataCRC(0)),o.Attributes.GetUserString('RhinoSceneFlow.Plant.v1')) for o in doc.Objects];assert before==after
reports={};modified=doc.Modified
for mode in ['individual','species','all']:
 api('configure_view',viewId=setup['view'],settings=dict(width=600,height=400,layers=[dict(kind='plants',plantGrouping=mode),dict(kind='shadow',blend='mul '),dict(kind='texture')],plantShadows=True))
 report=api('export_workbench',directory=os.path.join(folder,'final-'+mode),views=[setup['view']]);assert all(f['ok'] for f in report['files']),report;reports[mode]=report
assert doc.Modified==modified
# Actual reference-image input + reuse path; should return candidates without consuming another image generation.
job=api('material_chat_start',conversation='请提供一株美国红枫 Acer rubrum 的夏季绿叶透明 PNG 素材，树形与参考图片相同，先核实植物，再优先复用库里已有的相同素材。',referenceImages=[ai['job']['imagePath']],reuseSimilar=True)
with open(os.path.join(folder,'final-start.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,document=int(doc.RuntimeSerialNumber),reports=reports,reuseJob=job['id'],orientationReadOnly=True,modelRestored=True),f,indent=2)
print(json.dumps(dict(pid=EXPECTED_PID,nativeAlpha=True,threeOrientations=True,exports=list(reports.keys()),reuseJob=job['id'])))
