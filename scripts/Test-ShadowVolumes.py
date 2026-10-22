"""B-only volume exports, original-Brep oracle and known gap regression."""
import json,os,math,clr,System,Rhino
from Rhino.Geometry import Point3d,Vector3d,Line,LineCurve,Brep,Mesh,BoundingBox
from Rhino.Geometry.Intersect import Intersection
from Rhino.Display import DefinedViewportProjection
from Rhino.DocObjects import ViewportInfo
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;view=doc.Views.ActiveView;vp=view.ActiveViewport
folder=os.path.join(OUTPUT_DIR,'volumes-v041');os.makedirs(folder,exist_ok=True)
if doc.Objects.Count==0:
    source=Rhino.FileIO.File3dm.Read(os.path.join(OUTPUT_DIR,'alternatives','Shadow-Alternatives.3dm'))
    assert source is not None
    layer_map={}
    for old in source.AllLayers:
        layer=Rhino.DocObjects.Layer();layer.Name='Volumes_'+old.Name;layer.Color=old.Color
        layer_map[old.Index]=doc.Layers.Add(layer)
    for old in source.Objects:
        attrs=old.Attributes.Duplicate();attrs.LayerIndex=layer_map[old.Attributes.LayerIndex]
        attrs.SetUserString('SceneFlowShadowResearch','20261022')
        assert doc.Objects.Add(old.Geometry,attrs)!=System.Guid.Empty
assert all(o.Attributes.GetUserString('SceneFlowShadowResearch')=='20261022' for o in doc.Objects)
saved=ViewportInfo(vp);modified=doc.Modified
refs=[]
for o in doc.Objects:
    g=o.Geometry
    if isinstance(g,Brep):b=g
    elif isinstance(g,Mesh):b=Brep.CreateFromMesh(g,True)
    else:b=g.ToBrep()
    refs.append((o.Attributes.Name,b))
def api(operation,**kwargs):
    r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation=operation,document=int(doc.RuntimeSerialNumber),**kwargs))))
    assert r['ok'],r
    return r['result']
def snapshot():
    return (doc.Modified,doc.Objects.Count,tuple(str(o.Id) for o in doc.Objects.GetSelectedObjects(False,False)),str(vp.CameraLocation),str(vp.CameraDirection),str(vp.DisplayMode.Id),str(doc.RenderSettings.Sun.Vector),doc.RenderSettings.Sun.Enabled)
def trace(line):
    curve=LineCurve(line);best=None;distance=float('inf')
    try:
        for name,b in refs:
            ok,ts=Intersection.CurveBrep(curve,b,1e-6,1e-6)
            if ts:
                for t in ts:
                    p=curve.PointAt(t);d=p.DistanceTo(line.From)
                    if d<distance:distance=d;best=(name,b,p)
    finally:curve.Dispose()
    return best
def normal_at(b,p):
    distance=float('inf');normal=None
    for face in b.Faces:
        ok,u,v=face.ClosestPoint(p)
        if ok:
            d=face.PointAt(u,v).DistanceTo(p)
            if d<distance:distance=d;normal=face.NormalAt(u,v)
    return normal
def oracle(px,py,w,h,sun,form):
    ok,line=vp.GetFrustumLine(px*vp.Size.Width/w,py*vp.Size.Height/h);assert ok
    if line.From.DistanceTo(vp.CameraLocation)>line.To.DistanceTo(vp.CameraLocation):line=Line(line.To,line.From)
    result=trace(line)
    if result is None:return False,'background'
    name,b,p=result;n=normal_at(b,p)
    if n*line.Direction>0:n=-n
    if n*sun<=1e-9:return form,name
    hit=trace(Line(p+sun*1e-4,p+sun*1000))
    return hit is not None,name

report={'pid':EXPECTED_PID,'version':api('describe')['version'],'cases':[]}
assert report['version'] in ('0.4.1','0.5.0')
try:
 for name,top,form,width in [('top',True,False,1024),('perspective',False,False,1024),('form',False,True,512)]:
    if top:vp.SetProjection(DefinedViewportProjection.Top,'Volume_Top',True)
    else:
        vp.SetProjection(DefinedViewportProjection.Perspective,'Volume_Perspective',True)
        vp.SetCameraLocations(Point3d(11,0,2),Point3d(45,-48,36))
    vp.ZoomBoundingBox(BoundingBox(Point3d(-11,-7,-2),Point3d(34,7,10)))
    before=snapshot();light=[-.3,-1,1];sun=Vector3d(*light);sun.Unitize()
    result=api('export_shadow_psd',backend='volume',width=width,path=os.path.join(folder,name+'.psd'),overwrite=True,toSun=light,includeFormShading=form)
    assert before==snapshot(),'Export changed document/view'
    exp=result['export'];w=exp['width'];h=exp['height'];samples=[];used=set()
    def sample(x,y,label=None):
        if (x,y) in used:return
        expected,receiver=oracle(x+.5,y+.5,w,h,sun,form)
        if label and receiver!=label:return
        if all(oracle(x+.5+dx,y+.5+dy,w,h,sun,form)==(expected,receiver) for dx,dy in [(2,0),(-2,0),(0,2),(0,-2)]):
            samples.append(dict(x=x,y=y,shadow=expected,receiver=receiver));used.add((x,y))
    for gy in range(10):
        for gx in range(28):sample(int((gx+.5)*w/28),int((gy+.5)*h/10))
    for label,geometry in refs:
        if label in ('Ground','ShadowWall') or label.startswith('Counterexample'):continue
        pixels=[vp.WorldToClient(p) for p in geometry.GetBoundingBox(True).GetCorners()]
        left=max(0,min(p.X for p in pixels)*w/vp.Size.Width);right=min(w-1,max(p.X for p in pixels)*w/vp.Size.Width)
        top_edge=max(0,min(p.Y for p in pixels)*h/vp.Size.Height);bottom=min(h-1,max(p.Y for p in pixels)*h/vp.Size.Height)
        for gy in range(10):
            for gx in range(10):sample(int(left+(gx+.5)*(right-left)/10),int(top_edge+(gy+.5)*(bottom-top_edge)/10),label)
    base=api('export_psd',width=width,path=os.path.join(folder,'base-'+name+'.psd'),overwrite=True)
    report['cases'].append(dict(name=name,result=result,base=base,samples=samples,stateUnchanged=before==snapshot()))
    with open(os.path.join(folder,'report.json'),'w') as f:json.dump(report,f,indent=2)
 # Repeat the real smooth-normal contact fixture with both backends at exactly the same view.
 report['gap']=[]
 for label,x in [('smooth-receiver',100),('geometric-receiver',110)]:
    vp.SetProjection(DefinedViewportProjection.Top,'Volume_Gap',True)
    vp.ZoomBoundingBox(BoundingBox(Point3d(x-2,-2,0),Point3d(x+2,2,.25)))
    point=vp.WorldToClient(Point3d(x,0,0))
    entry=dict(name=label)
    for backend in ['ray','volume']:
        result=api('export_shadow_psd',backend=backend,width=1024,path=os.path.join(folder,'gap-'+label+'-'+backend+'.psd'),overwrite=True,toSun=[1,0,1])
        data=result['export'];entry[backend]=result
        entry['probe']=[int(point.X*data['width']/vp.Size.Width),int(point.Y*data['height']/vp.Size.Height)]
    report['gap'].append(entry)
 # New command, style and invalid backend contract.
 vp.SetProjection(DefinedViewportProjection.Perspective,'Volume_Final',True)
 vp.SetCameraLocations(Point3d(11,0,2),Point3d(45,-48,36));vp.ZoomBoundingBox(BoundingBox(Point3d(-11,-7,-2),Point3d(34,7,10)))
 # The shared light selection must work for the volume backend too.
 render_state=doc.RenderSettings.Duplicate();sun_hash=int(doc.RenderSettings.Sun.Hash);sun=doc.RenderSettings.Sun
 try:
    sun.BeginChange(Rhino.Render.RenderContent.ChangeContexts.Program)
    try:sun.ManualControlOn=True;sun.Azimuth=135;sun.Altitude=45;sun.Enabled=True
    finally:sun.EndChange()
    assert abs(sun.Altitude-45)<1e-8 and abs(sun.Vector.Z+math.sqrt(.5))<1e-8
    automatic=api('export_shadow_psd',backend='volume',width=128,path=os.path.join(folder,'sun-auto.psd'),overwrite=True)
    explicit=api('export_shadow_psd',backend='volume',width=128,path=os.path.join(folder,'sun-explicit.psd'),overwrite=True,toSun=automatic['toSun'])
    assert automatic['lightSource']=='rhino_sun'
    with open(automatic['export']['path'],'rb') as f:reference=f.read()
    with open(explicit['export']['path'],'rb') as f:assert f.read()==reference
    report['sun']=dict(samePsdBytes=True,altitude=sun.Altitude,azimuth=sun.Azimuth)
 finally:
    doc.RenderSettings=render_state;render_state.Dispose();assert int(doc.RenderSettings.Sun.Hash)==sun_hash
    report['sun']['settingsRestored']=True
 report['defaultResolution']=api('export_shadow_psd',backend='volume',path=os.path.join(folder,'default-2048.psd'),overwrite=True,toSun=[-.3,-1,1])
 report['style']=api('export_shadow_psd',backend='volume',width=128,path=os.path.join(folder,'style.psd'),overwrite=True,toSun=[-.3,-1,1],color='#123456',opacity=.5)
 directory=api('status')['defaultDirectory'];before_files=set(os.listdir(directory));before=snapshot()
 assert Rhino.RhinoApp.RunScript('_-RhinoSceneFlowExportShadowVolumePSD 128 _Enter',False)
 created=[os.path.join(directory,f) for f in set(os.listdir(directory))-before_files if f.endswith('.psd')]
 assert len(created)==1 and snapshot()==before,created
 report['commandPath']=created[0]
 invalid=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='export_shadow_psd',document=int(doc.RuntimeSerialNumber),backend='invalid',width=64))))
 assert not invalid['ok'];report['invalidBackendRejected']=True
 report['complete']=True
finally:
 vp.SetViewProjection(saved,True);saved.Dispose();doc.Modified=modified
 report['viewRestored']=True
 with open(os.path.join(folder,'report.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps({'complete':report.get('complete',False),'pid':EXPECTED_PID,'timings':[(c['name'],c['result']['export']['elapsedMilliseconds']) for c in report['cases']]}))
