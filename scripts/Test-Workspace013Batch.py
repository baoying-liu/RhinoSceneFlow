"""Final delivered UI: multiple thumbnails, preset/copy controls and a real two-view async PSD batch."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,ExportPanelController
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'workspace013')
def api(op,**kw):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=op,document=int(doc.RuntimeSerialNumber),**kw))))
 assert r['ok'],r
 return r['result']
assert doc.Path.endswith('SceneFlow-Workspace013.3dm')
doc.NamedViews.Add('SceneFlow_UI013_2',doc.Views.ActiveView.ActiveViewport.Id)
api('material_workspace_open',page='export');p=ExportPanelController.Find(doc.RuntimeSerialNumber);p.RefreshNamedViews();assert p.Views.Count==2
first=p.Views[0].Copy();second=p.Views[1].Copy();flags=BindingFlags.Instance|BindingFlags.NonPublic
cards=p.GetType().GetField('cards',flags).GetValue(p);c=cards[first.Id];presets=c.GetType().GetField('presets',flags).GetValue(c);presets.SelectedKey='2048'
assert max(p.Views[0].Width,p.Views[0].Height)==2048
p.CopySize(first.Id);p.PasteSize(second.Id);assert p.Views[1].Width==p.Views[0].Width and p.Views[1].Height==p.Views[0].Height
p.CopyLayers(first.Id);p.PasteLayers(second.Id);assert p.Views[1].Layers.Count==3 and not System.Object.ReferenceEquals(p.Views[0].Layers[0],p.Views[1].Layers[0])
p.SetView(first);p.CopySize(first.Id);p.PasteSize(second.Id)
v=doc.Views.ActiveView.ActiveViewport;beforeCamera=str(v.CameraLocation);beforeSun=int(doc.RenderSettings.Sun.Hash);nativeViews=len(doc.Views.GetViewList(True,True))
p.OpenDetails(first.Id);p.CloseDetails();assert beforeCamera==str(v.CameraLocation) and beforeSun==int(doc.RenderSettings.Sun.Hash) and nativeViews==len(doc.Views.GetViewList(True,True))
for r in p.Views:p.RefreshCard(r.Id)
state=api('panel_status');assert all(v['loaded'] for v in state['previews'])
out=os.path.join(folder,'delivered-batch-'+str(System.Guid.NewGuid())[:8]);p.GetType().GetField('folder',flags).GetValue(p).Text=out
System.AppDomain.CurrentDomain.SetData('Workspace013ExportBefore',json.dumps([doc.Objects.Count,doc.Modified,str(v.CameraLocation),int(doc.RenderSettings.Sun.Hash)]));task=p.StartExport();System.AppDomain.CurrentDomain.SetData('Workspace013ExportTask',task)
report=dict(pid=EXPECTED_PID,views=2,allPreviews=True,sizePreset=True,sizeCopy=True,layerCopyDeep=True,detailsPreserveNativeState=True,batchStarted=True)
with open(os.path.join(folder,'batch-ui-verified.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
