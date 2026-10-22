"""Fixed B: native Eto panel plus Named View batch exports, no mouse."""
import clr,Rhino,System,os,json
from Rhino.Geometry import Point3d,BoundingBox
from Rhino.DocObjects import ViewportInfo,ViewInfo
from Rhino.Display import DefinedViewportProjection,DisplayModeDescription
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi,ExportPanelController
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;vp=doc.Views.ActiveView.ActiveViewport
folder=os.path.join(OUTPUT_DIR,'panel');os.makedirs(folder,exist_ok=True)
if doc.Objects.Count==0:
    source=Rhino.FileIO.File3dm.Read(os.path.join(OUTPUT_DIR,'alternatives','Shadow-Alternatives.3dm'))
    assert source is not None
    layers={}
    for old in source.AllLayers:
        layer=Rhino.DocObjects.Layer();layer.Name='Panel_'+old.Name;layer.Color=old.Color
        layers[old.Index]=doc.Layers.Add(layer)
    for old in source.Objects:
        attrs=old.Attributes.Duplicate();attrs.LayerIndex=layers[old.Attributes.LayerIndex]
        attrs.SetUserString('SceneFlowShadowResearch','20261022')
        assert doc.Objects.Add(old.Geometry,attrs)!=System.Guid.Empty
assert all(o.Attributes.GetUserString('SceneFlowShadowResearch')=='20261022' for o in doc.Objects)

def api(operation,**kwargs):
    result=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=operation,document=int(doc.RuntimeSerialNumber),**kwargs))))
    assert result['ok'],result
    return result['result']

def state():
    return (doc.Modified,doc.Objects.Count,doc.NamedViews.Count,str(vp.CameraLocation),str(vp.CameraDirection),
        str(vp.DisplayMode.Id),vp.Size.Width,vp.Size.Height,
        tuple(str(o.Id) for o in doc.Objects.GetSelectedObjects(False,False)),
        tuple((str(l.Id),l.Color.ToArgb(),l.IsVisible) for l in doc.Layers if not l.IsDeleted))

report=dict(pid=EXPECTED_PID,version=api('describe')['version'],cases=[])
assert report['version']=='0.5.0'
saved=ViewportInfo(vp)
try:
    cases=[('SceneFlow_Test_俯视',True,320,200),('SceneFlow_Test_透视',False,384,192),('SceneFlow_Test_方图',False,240,240)]
    entries=[]
    for name,top,w,h in cases:
        if top:vp.SetProjection(DefinedViewportProjection.Top,'Panel_Test_Top',True)
        else:
            vp.SetProjection(DefinedViewportProjection.Perspective,'Panel_Test_Perspective',True)
            vp.SetCameraLocations(Point3d(11,0,2),Point3d(45,-48,36))
        vp.ZoomBoundingBox(BoundingBox(Point3d(-11,-7,-2),Point3d(34,7,10)))
        old=doc.NamedViews.FindByName(name)
        if old>=0:assert doc.NamedViews.Delete(old)
        info=ViewInfo(vp);info.Name=name;info.Viewport.FrustumAspect=float(w)/h
        index=doc.NamedViews.Add(info);info.Dispose();assert index>=0
        named=doc.NamedViews[index]
        entries.append(dict(viewId=str(named.NamedViewId),width=w,height=h,name=name))
        named.Dispose()
finally:vp.SetViewProjection(saved,True);saved.Dispose()

before=state();listed=api('named_views')
assert set(e['viewId'] for e in entries).issubset({v['id'] for v in listed})
assert before==state()
run_folder=os.path.join(folder,'run-'+str(System.Guid.NewGuid()).split('-')[0]);os.makedirs(run_folder,exist_ok=True)
out=os.path.join(run_folder,'batch');os.makedirs(out,exist_ok=True)
sentinel=os.path.join(out,entries[0]['name']+'.psd')
with open(sentinel,'wb') as f:f.write(b'keep-existing-original')
with open(os.path.join(out,entries[0]['name']+'001.psd'),'wb') as f:f.write(b'keep-existing-001')
views=[{k:v for k,v in e.items() if k!='name'} for e in entries]
batch=api('export_named_views',views=views,directory=out,collision='number')
assert not batch['cancelled'] and all(f['ok'] for f in batch['files']),batch
assert os.path.basename(batch['files'][0]['path'])==entries[0]['name']+'002.psd'
with open(sentinel,'rb') as f:assert f.read()==b'keep-existing-original'
with open(os.path.join(folder,'state-audit.json'),'w') as f:json.dump(dict(before=before,after=state()),f,indent=2)
assert before==state(),'Batch changed document/view'
report['entries']=entries;report['combined']=batch
for channels,label in [(['material'],'material'),(['shadow'],'shadow')]:
    case=api('export_named_views',views=views[:1],directory=os.path.join(run_folder,label),channels=channels)
    assert all(f['ok'] for f in case['files']),case
    report['cases'].append(dict(channels=channels,result=case))
    assert before==state()
numbered=api('export_named_views',views=views[:1],directory=out,channels=['material'])
assert os.path.basename(numbered['files'][0]['path'])==entries[0]['name']+'003.psd'
report['numbered']=numbered
overwrite=api('export_named_views',views=views[:1],directory=out,channels=['material'],collision='overwrite')
assert overwrite['files'][0]['path']==sentinel and overwrite['files'][0]['ok']
report['overwrite']=overwrite
before_files=set(os.listdir(out))
cancelled=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='export_named_views',document=int(doc.RuntimeSerialNumber),views=views,directory=out,collision='cancel'))))
assert not cancelled['ok'] and before_files==set(os.listdir(out))
assert before==state()
for bad in [dict(views=[dict(views[0],width=0)],channels=['material']),dict(views=views,channels=[]),dict(views=views,channels=['bad'])]:
    result=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='export_named_views',document=int(doc.RuntimeSerialNumber),directory=out,**bad))))
    assert not result['ok'],result

assert Rhino.RhinoApp.RunScript('_RhinoSceneFlowPanel',False)
panel=ExportPanelController.Find(doc.RuntimeSerialNumber);assert panel is not None
opened=api('open_panel');assert len(opened['views'])==len(listed)
assert ExportPanelController.Find(doc.RuntimeSerialNumber)==panel
panel.SelectNamedView(System.Guid(entries[1]['viewId']))
assert before==state(),'Panel preview modified the main Rhino view'
report['stateUnchanged']=True;report['panel']=api('panel_status');report['complete']=True
with open(os.path.join(folder,'report.json'),'w',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(complete=True,report=os.path.join(folder,'report.json'),panel=report['panel'])))
