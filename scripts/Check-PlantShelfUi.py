import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin');clr.AddReference('PresentationCore');clr.AddReference('PresentationFramework');clr.AddReference('WindowsBase')
from RhinoSceneFlow.Plugin import McpApi
from System.Windows import Size,Rect
from System.Windows.Media import PixelFormats
from System.Windows.Media.Imaging import RenderTargetBitmap,PngBitmapEncoder,BitmapFrame
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'plants0161');setup=json.load(open(os.path.join(folder,'setup.json')))
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assets=api('plant_library')['assets'];assert all(a['plant']['names'].get('en') and a['plant']['names'].get('zh') for a in assets),'Names still pending; check catalog job'
for a in assets:
 old=next(o for o in setup['before'] if o['id']==a['id'])
 assert a['revision']==old['revision'] and a['sha256']==old['sha256'] and a['maps']==old['maps'] and a['heightMeters']==old['heightMeters']
 assert a['plant']['scientificName']==old['plant']['scientificName'] and a['plant']['spacingMeters']==old['plant']['spacingMeters']
def capture(file):
 state=api('material_workspace_status');panel=Rhino.UI.Panels.GetPanel(System.Guid(state['pages'][3]['panelId']));root=panel.ControlObject;root.Measure(Size(420,1100));root.Arrange(Rect(0,0,420,1100));root.UpdateLayout();b=RenderTargetBitmap(630,1650,144,144,PixelFormats.Pbgra32);b.Render(root);encoder=PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(b));stream=System.IO.FileStream(os.path.join(folder,file),System.IO.FileMode.Create)
 try:encoder.Save(stream)
 finally:stream.Dispose()
 return state['tools']['planting']['details']
zh=capture('tiles-zh.png');assert zh['libraryShelf']['count']==zh['compositionShelf']['count']==3 and zh['libraryShelf']['view']=='tiles'
assert abs(next(p for p in zh['palette'] if p['asset']==setup['lastAsset'])['spacingMeters']-6)<1e-9
api('plant_ui_settings',settings=dict(language='en',libraryView='list',compositionView='list'))
en=capture('list-en.png');assert en['libraryShelf']['view']==en['compositionShelf']['view']=='list'
z={p['id']:p for p in zh['libraryShelf']['items']};e={p['id']:p for p in en['libraryShelf']['items']};assert set(z)==set(e)
for a in assets:
 assert z[a['id']]['latin']==e[a['id']]['latin']==a['plant']['scientificName'];assert e[a['id']]['name']==a['plant']['names']['en']
assert abs(next(p for p in en['palette'] if p['asset']==setup['lastAsset'])['spacingMeters']-6)<1e-9
api('plant_ui_settings',settings=dict(language='en',libraryView='tiles',compositionView='tiles'));capture('tiles-en.png')
assert not doc.Modified
with open(os.path.join(folder,'ui-verified.json'),'w') as f:json.dump(dict(pid=EXPECTED_PID,tilesZh=zh['libraryShelf'],listEn=en['libraryShelf'],manualParameterPreserved=True,namingPreservedAppearance=True,documentUnchanged=True),f,indent=2)
print('Three thumbnail cards, list/grid switch, bilingual names, fixed Latin and manual spacing preservation passed')
