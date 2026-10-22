"""Live shadow export and exact Rhino Brep oracle; sandbox B only, no mouse."""
import json, os, math
import clr, System, Rhino
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Plugin import McpApi
from Rhino.Geometry import Point3d, Vector3d, Line, LineCurve, Brep, Mesh, BoundingBox
from Rhino.Geometry.Intersect import Intersection
from Rhino.Display import DefinedViewportProjection
assert System.Diagnostics.Process.GetCurrentProcess().Id == EXPECTED_PID
doc=__rhino_doc__;view=doc.Views.ActiveView;vp=view.ActiveViewport
assert len(list(doc.Objects))>=7
assert all(o.Attributes.GetUserString('SceneFlowComplexTest')=='v1' for o in doc.Objects)
folder=os.path.join(OUTPUT_DIR,'shadows');os.makedirs(folder,exist_ok=True)
wall=next((o for o in doc.Objects if o.Attributes.Name=='ShadowWall'),None)
if wall is None:
    a=Rhino.DocObjects.ObjectAttributes();a.Name='ShadowWall';a.SetUserString('SceneFlowComplexTest','v1')
    wall_id=doc.Objects.AddBrep(Brep.CreateFromCornerPoints(Point3d(-11,6,-2),Point3d(34,6,-2),Point3d(34,6,10),Point3d(-11,6,10),1e-6),a)
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
for name,top,light,form,width in [('top',True,(-.3,-1,1),False,1024),('perspective',False,(-.3,-1,1),False,1024),('form',False,(-.3,-1,1),True,512),('other-sun',False,(1,-1,2),False,512)]:
    if top:vp.SetProjection(DefinedViewportProjection.Top,'Shadow_Top',True)
    else:
        vp.SetProjection(DefinedViewportProjection.Perspective,'Shadow_Perspective',True)
        vp.SetCameraLocations(Point3d(11,0,2),Point3d(45,-48,36))
    vp.ZoomBoundingBox(BoundingBox(Point3d(-11,-7,-2),Point3d(34,7,10)));doc.Views.Redraw()
    before=snapshot();path=os.path.join(os.path.dirname(OUTPUT_DIR),'exports','shadow-'+name+'.psd')
    result=api('export_shadow_psd',width=width,path=path,overwrite=True,viewportId=str(vp.Id),toSun=list(light),includeFormShading=form,color='#5A5A5A')
    assert before==snapshot(),'Export modified model or view'
    exp=result['export'];w=exp['width'];h=exp['height'];sun=Vector3d(*light);sun.Unitize()
    samples=[]
    for gy in range(14):
        for gx in range(40):
            x=int((gx+.5)*w/40);y=int((gy+.5)*h/14)
            expected,receiver=oracle(x+.5,y+.5,w,h,sun,form)
            if all(oracle(x+.5+dx,y+.5+dy,w,h,sun,form)[0]==expected for dx,dy in [(2,0),(-2,0),(0,2),(0,-2)]):
                samples.append(dict(x=x,y=y,shadow=expected,receiver=receiver))
    # Focus on each curved object's projected bounds so small self/cross shadows
    # are exercised, rather than letting empty background dominate the oracle.
    used={(s['x'],s['y']) for s in samples}
    for label,geometry in refs:
        if label in ('Ground','ShadowWall'):continue
        pixels=[vp.WorldToClient(p) for p in geometry.GetBoundingBox(True).GetCorners()]
        left=max(0,min(p.X for p in pixels)*w/vp.Size.Width);right=min(w-1,max(p.X for p in pixels)*w/vp.Size.Width)
        top_edge=max(0,min(p.Y for p in pixels)*h/vp.Size.Height);bottom=min(h-1,max(p.Y for p in pixels)*h/vp.Size.Height)
        for gy in range(12):
            for gx in range(12):
                x=int(left+(gx+.5)*(right-left)/12);y=int(top_edge+(gy+.5)*(bottom-top_edge)/12)
                if (x,y) in used:continue
                expected,receiver=oracle(x+.5,y+.5,w,h,sun,form)
                if receiver!=label:continue
                if all(oracle(x+.5+dx,y+.5+dy,w,h,sun,form)==(expected,receiver) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]):
                    samples.append(dict(x=x,y=y,shadow=expected,receiver=receiver));used.add((x,y))
    aligned=api('export_psd',width=width,path=os.path.join(os.path.dirname(OUTPUT_DIR),'exports','shadow-base-'+name+'.psd'),overwrite=True)
    assert aligned['width']==w and aligned['height']==h and before==snapshot()
    report['cases'].append(dict(name=name,result=result,base=aligned,samples=samples,stateUnchanged=True))
    with open(os.path.join(folder,'report.json'),'w') as f:json.dump(report,f,indent=2)
before=snapshot()
report['defaultResolution']=api('export_shadow_psd',path=os.path.join(os.path.dirname(OUTPUT_DIR),'exports','shadow-default-2048.psd'),overwrite=True,toSun=[-.3,-1,1])
assert report['defaultResolution']['export']['width']==2048 and before==snapshot()
# Verify the Rhino Sun convention and the automatic source branch without leaving
# solar settings or the document modified flag changed after this test.
sun=doc.RenderSettings.Sun
render_state=doc.RenderSettings.Duplicate();sun_hash=int(sun.Hash);saved_modified=doc.Modified
try:
    sun.BeginChange(Rhino.Render.RenderContent.ChangeContexts.Program)
    try:
        sun.ManualControlOn=True;sun.Azimuth=135;sun.Altitude=45;sun.Enabled=True
    finally:sun.EndChange()
    assert sun.ManualControlOn and abs(sun.Altitude-45)<1e-8 and abs(sun.Azimuth-135)<1e-8
    assert abs(sun.Vector.Z+math.sqrt(.5))<1e-8
    before=snapshot();v=sun.Vector
    automatic=api('export_shadow_psd',width=128,path=os.path.join(os.path.dirname(OUTPUT_DIR),'exports','shadow-rhino-sun.psd'),overwrite=True)
    assert automatic['lightSource']=='rhino_sun',automatic
    expected=Vector3d(-v.X,-v.Y,-v.Z);expected.Unitize()
    assert all(abs(a-b)<1e-10 for a,b in zip(automatic['toSun'],[expected.X,expected.Y,expected.Z]))
    explicit=api('export_shadow_psd',width=128,path=os.path.join(os.path.dirname(OUTPUT_DIR),'exports','shadow-explicit-sun.psd'),overwrite=True,toSun=automatic['toSun'])
    assert before==snapshot()
    with open(automatic['export']['path'],'rb') as f:automatic_bytes=f.read()
    with open(explicit['export']['path'],'rb') as f:assert f.read()==automatic_bytes
    report['sun']=dict(automatic=automatic,explicit=explicit,identical=True)
finally:
    doc.RenderSettings=render_state
    assert int(doc.RenderSettings.Sun.Hash)==sun_hash
    doc.Modified=saved_modified;render_state.Dispose()
before=snapshot()
report['style']=api('export_shadow_psd',width=128,path=os.path.join(os.path.dirname(OUTPUT_DIR),'exports','shadow-styled.psd'),overwrite=True,toSun=[-.3,-1,1],color='#123456',opacity=.5)
assert before==snapshot()
# Invalid direction/style must fail before writing any file.
for extra in [dict(toSun=[0,0,0]),dict(opacity=0),dict(bias=-1),dict(color='bad')]:
    r=json.loads(McpApi.Execute(json.dumps(dict(apiVersion=1,operation='export_shadow_psd',document=int(doc.RuntimeSerialNumber),width=64,**extra))))
    assert not r['ok'],r
# Default command uses the persisted directory, without file dialogs.
directory=api('status')['defaultDirectory'];before_files=set(os.listdir(directory))
assert Rhino.RhinoApp.RunScript('_-RhinoSceneFlowExportShadowPSD 128 _Enter',False)
created=[os.path.join(directory,f) for f in set(os.listdir(directory))-before_files if f.endswith('.psd')]
assert len(created)==1,created
report['commandPath']=created[0]
report['complete']=True
options=Rhino.FileIO.FileWriteOptions();options.SuppressDialogBoxes=True
doc.WriteFile(os.path.join(folder,'Shadow-Test.3dm'),options)
with open(os.path.join(folder,'report.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps({'complete':True,'report':os.path.join(folder,'report.json'),'timings':[(c['name'],c['result']['export']['elapsedMilliseconds']) for c in report['cases']]}))
