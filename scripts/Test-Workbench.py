"""B-only v0.6 contracts, real Eto cards, copy/paste, detail controls and disk/tile exports."""
import Rhino,System,clr,json,os
from System.Reflection import BindingFlags
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,ExportPanelController
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;folder=os.path.join(OUTPUT_DIR,'workbench');os.makedirs(folder,exist_ok=True)
if doc.Objects.Count==0:
 source=Rhino.FileIO.File3dm.Read(os.path.join(OUTPUT_DIR,'direct','benchmark-scene.3dm'));assert source is not None
 mapping={}
 for old in source.AllLayers:
  layer=Rhino.DocObjects.Layer();layer.Name='Workbench_'+old.Name;layer.Color=old.Color;mapping[old.Index]=doc.Layers.Add(layer)
 for old in source.Objects:
  a=old.Attributes.Duplicate();a.LayerIndex=mapping[old.Attributes.LayerIndex];assert doc.Objects.Add(old.Geometry,a)!=System.Guid.Empty
 doc.RenderSettings=source.Settings.RenderSettings
 for old in source.NamedViews:doc.NamedViews.Add(old)
 source.Dispose()
assert doc.NamedViews.Count>=2
def api(operation,**kwargs):
 r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=operation,document=int(doc.RuntimeSerialNumber),**kwargs))))
 assert r['ok'],r
 return r['result']
def state():
 v=doc.Views.ActiveView.ActiveViewport
 return (doc.Modified,doc.Objects.Count,str(v.CameraLocation),str(v.CameraDirection),str(v.CameraUp),str(v.GetFrustum()),str(v.Size),v.Name,str(v.DisplayMode.Id),
  int(doc.RenderSettings.Sun.Hash),tuple(str(o.Id) for o in doc.Objects.GetSelectedObjects(False,False)),tuple((str(v.MainViewport.Id),v.Floating) for v in doc.Views.GetViewList(True,True)))
def field(obj,name):return obj.GetType().GetField(name,BindingFlags.Instance|BindingFlags.NonPublic).GetValue(obj)
def prop(obj,name):return obj.GetType().GetProperty(name,BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic).GetValue(obj)
def walk(obj):
 yield obj
 if hasattr(obj,'Controls'):
  for c in obj.Controls:
   for v in walk(c):yield v
def click(button):button.GetType().GetMethod('PerformClick').Invoke(button,None)
assert api('describe')['version']=='0.6.0'
settings=api('workbench_settings');original=settings['views'];ids=[v['id'] for v in original]
shaded=next(m['id'] for m in settings['displayModes'] if m['name']=='Shaded')
rendered=next(m['id'] for m in settings['displayModes'] if m['name']=='Rendered')
arctic=next(m['id'] for m in settings['displayModes'] if m['name']=='Arctic')
before=state();report=dict(pid=EXPECTED_PID,version='0.6.0',original=original)
try:
 first=api('configure_view',viewId=ids[0],settings=dict(width=320,height=200,mode=shaded,layers=[dict(kind='shadow',blend='mul ',opacity=60),dict(kind='material'),dict(kind='display',mode=shaded)],camera=dict(yaw=8,pitch=-4,zoom=1.1),sun=dict(useDocument=False,azimuth=120,altitude=35)))
 second=api('configure_view',viewId=ids[1],settings=dict(width=240,height=240,mode=arctic,layers=[dict(kind='shadow',opacity=50),dict(kind='display',mode=rendered)]))
 assert state()==before,'Configure changed Rhino state'
 out=os.path.join(folder,'run-'+str(System.Guid.NewGuid())[:8]);os.makedirs(out)
 report['export']=api('export_workbench',directory=out,views=ids[:2]);assert all(f['ok'] for f in report['export']['files']),report['export']
 report['settings']=[first,second];assert state()==before,'Export changed Rhino state'
 bad=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='configure_view',document=int(doc.RuntimeSerialNumber),viewId=ids[0],settings=dict(layers=[dict(kind='')])))))
 assert not bad['ok'];report['placeholderRejected']=True
 p=ExportPanelController.Open(doc);assert p.Views.Count==doc.NamedViews.Count
 for id in ids:p.RefreshCard(System.Guid(id))
 card=field(p,'cards')[System.Guid(ids[0])]
 add=next(c for c in walk(prop(card,'Root')) if c.GetType().Name=='Button' and c.Text=='＋ 添加图层');click(add)
 assert p.Views[0].Layers[p.Views[0].Layers.Count-1].Kind==''
 delete=[c for c in walk(field(card,'layerHost')) if c.GetType().Name=='Button' and c.Text=='×'][-1];click(delete)
 assert p.Views[0].Layers.Count==3
 p.CopyLayers(System.Guid(ids[0]));p.PasteLayers(System.Guid(ids[1]))
 assert p.Views[1].Layers.Count==3 and p.Views[1].Width==240
 assert p.Views[1].Camera.Yaw==0 and p.Views[1].Mode==System.Guid(arctic)
 p.Views[0].Layers[0].Opacity=61;assert p.Views[1].Layers[0].Opacity==60,'Paste aliased source layers'
 presets=field(card,'presets')
 for key,n in [('1024',1024),('2048',2048),('4096',4096),('8192',8192)]:
  presets.SelectedKey=key;assert max(p.Views[0].Width,p.Views[0].Height)==n
 p.CopySize(System.Guid(ids[0]));p.PasteSize(System.Guid(ids[1]));assert (p.Views[1].Width,p.Views[1].Height)==(8192,5120)
 p.OpenDetails(System.Guid(ids[0]));detail=field(p,'detail');field(detail,'yaw').Value=14;field(detail,'documentSun').Checked=False;field(detail,'azimuth').Value=210;field(detail,'altitude').Value=25
 assert p.Views[0].Camera.Yaw==14 and p.Views[0].Sun.Azimuth==210
 p.CapturePreview(System.Guid(ids[0]),os.path.join(folder,'details-adjusted.png'));p.CloseDetails();assert state()==before
 saved=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='panel_status',document=int(doc.RuntimeSerialNumber)))))['result']['views']
 p.Close();p=ExportPanelController.Open(doc);reopened=api('panel_status')['views'];assert [(v['id'],v['width'],v['layers']) for v in saved]==[(v['id'],v['width'],v['layers']) for v in reopened]
 report['ui']=dict(allCards=True,addDelete=True,preset8k=True,layersDeepCopied=True,sizeIndependent=True,detailCameraSun=True,persisted=True)
 # Restore per-view user settings before a separately named seam audit.
 for r in original:api('configure_view',viewId=r['id'],settings=r)
 seam=api('configure_view',viewId=ids[1],settings=dict(width=1200,height=720,layers=[dict(kind='shadow'),dict(kind='material')],camera=dict(yaw=0,pitch=0,zoom=1,panX=0,panY=0,panZ=0),sun=dict(useDocument=True)))
 report['seam']=api('export_workbench',directory=os.path.join(out,'tiled'),views=[ids[1]])
 report['seamReference']=api('export_named_views',directory=os.path.join(out,'reference'),views=[dict(viewId=ids[1],width=1200,height=720)],channels=['material','shadow'])
 assert all(f['ok'] for f in report['seam']['files']+report['seamReference']['files'])
 assert state()==before
 report['stateUnchanged']=True;report['complete']=True
finally:
 for r in original:
  try:api('configure_view',viewId=r['id'],settings=r)
  except Exception:pass
 report['finalStateUnchanged']=state()==before
 with open(os.path.join(folder,'report.json'),'w',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(complete=report.get('complete'),ui=report.get('ui'),files=report.get('export'),stateUnchanged=report['finalStateUnchanged'])))
