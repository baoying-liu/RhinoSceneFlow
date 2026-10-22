"""Exercise real Eto controls via the plugin's own objects; no desktop input."""
import clr,Rhino,System,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import ExportPanelController,McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;p=ExportPanelController.Find(doc.RuntimeSerialNumber);assert p is not None
folder=os.path.join(OUTPUT_DIR,'panel')
with open(os.path.join(folder,'report.json'),encoding='utf-8') as f:report=json.load(f)
def field(name):return p.GetType().GetField(name,BindingFlags.Instance|BindingFlags.NonPublic).GetValue(p)
def state():return json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='panel_status',document=int(doc.RuntimeSerialNumber)))))['result']
before=(doc.Modified,str(doc.Views.ActiveView.ActiveViewport.CameraLocation),str(doc.Views.ActiveView.ActiveViewport.Size),str(doc.Views.ActiveView.ActiveViewport.DisplayMode.Id))
p.SelectNamedView(System.Guid(report['entries'][1]['viewId']))
assert str(state()['selected'])==report['entries'][1]['viewId']
field('width').Value=352;field('height').Value=224
s=state();edited=next(v for v in s['views'] if v['id']==report['entries'][1]['viewId'])
assert (edited['width'],edited['height'])==(352,224),s
p.RefreshNamedViews();s=state();edited=next(v for v in s['views'] if v['id']==report['entries'][1]['viewId'])
assert (edited['width'],edited['height'])==(352,224),'Refresh lost per-view dimensions'
captured=[]
for name in ['Shaded','Rendered','Arctic']:
    mode=next(m for m in s['displayModes'] if m['name']==name)
    field('modes').SelectedKey=mode['id'];p.RefreshPreview()
    path=os.path.join(folder,'preview-'+name.lower()+'.png');p.CapturePreview(path)
    captured.append(dict(mode=name,path=path))
assert before==(doc.Modified,str(doc.Views.ActiveView.ActiveViewport.CameraLocation),str(doc.Views.ActiveView.ActiveViewport.Size),str(doc.Views.ActiveView.ActiveViewport.DisplayMode.Id))
report['ui']=dict(dimensionsPreserved=True,previews=captured,stateUnchanged=True,state=state())
with open(os.path.join(folder,'report.json'),'w',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(report['ui']))
