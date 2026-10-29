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
ai=json.load(open(os.path.join(folder,'ai-status.json')))
assert ai['chat']['status']=='completed' and os.path.isfile(ai['chat']['imagePath'])
asset=next(a for a in ai['library']['assets'] if a['id']==ai['chat']['material'])
assert asset['randomization']['mode']=='auto' and asset['randomization']['recommendedBy']=='ai' and asset['randomization']['recommendedMode']=='stochastic'
assert ai['brick']['randomization']['mode']=='structured' and not ai['brick']['randomization']['rotate']
state=api('material_workspace_group');assert all(t['error'] is None for t in state['tools'].values())
api('material_tool_select',assetId=asset['id']);api('material_shelf_open')
panel=Rhino.UI.Panels.GetPanel(System.Guid(state['pages'][1]['panelId']))
tool=panel.GetType().GetProperty('Tool',BindingFlags.Instance|BindingFlags.NonPublic).GetValue(panel)
field=lambda n:tool.GetType().GetField(n,BindingFlags.Instance|BindingFlags.NonPublic).GetValue(tool)
assert field('randomMode').SelectedKey=='auto'
field('randomSettings').Expanded=True
root=panel.ControlObject;root.Measure(Size(420,950));root.Arrange(Rect(0,0,420,950));root.UpdateLayout()
bitmap=RenderTargetBitmap(630,1425,144,144,PixelFormats.Pbgra32);bitmap.Render(root)
encoder=PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(bitmap));stream=System.IO.FileStream(os.path.join(folder,'random-ui.png'),System.IO.FileMode.Create)
try:encoder.Save(stream)
finally:stream.Dispose()
# Cancel immediately while the UI cannot dispatch completion; no document commit is allowed.
before=api('material_inspect',objects=setup['objects'])
job=api('material_random_prepare',assetId=asset['id'],preview=True)
api('material_random_cancel',jobId=job['id'])
assert before==api('material_inspect',objects=setup['objects'])
# Override through actual Eto controls; primary Apply must save the draft automatically.
api('material_tool_select',assetId=setup['asset']['id'])
field('randomMode').SelectedKey='macro';field('randomTiles').SelectedKey='2';field('randomSeed').Value=88
field('apply').PerformClick()
with open(os.path.join(folder,'ui-start.json'),'w') as f:json.dump(dict(cancelJob=job['id'],aiDefaultVerified=True,brickStructureVerified=True,manualOverrideStarted=True),f,indent=2)
print('AI defaults, native UI capture, cancellation and manual override started')
