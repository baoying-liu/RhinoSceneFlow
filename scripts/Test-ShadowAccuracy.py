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
folder=os.path.join(OUTPUT_DIR,'accuracy');os.makedirs(folder,exist_ok=True)
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
            def roots(aa,bb,cc):
                if abs(aa)<1e-20:return [] if abs(bb)<1e-20 else [-cc/bb]
                disc=bb*bb-4*aa*cc
                return [] if disc<0 else [(-bb-math.sqrt(disc))/(2*aa),(-bb+math.sqrt(disc))/(2*aa)]
            o=line.From;d=line.Direction;values=None
            if name=='Hyperboloid':
                k=27.0/49
                values=roots(d.X*d.X+d.Y*d.Y-k*d.Z*d.Z,2*((o.X-11)*d.X+o.Y*d.Y-k*(o.Z-3.5)*d.Z),(o.X-11)**2+o.Y**2-k*(o.Z-3.5)**2-2.25)
                values=[t for t in values if 0<=line.PointAt(t).Z<=7]
            elif name=='ShadowWall':
                values=[] if abs(d.Y)<1e-20 else [(6-o.Y)/d.Y]
                values=[t for t in values if -11<=line.PointAt(t).X<=34 and -2<=line.PointAt(t).Z<=10]
            elif name=='Ground':
                values=[] if abs(d.Z)<1e-20 else [(-2-o.Z)/d.Z]
                values=[t for t in values if -11<=line.PointAt(t).X<=34 and -7<=line.PointAt(t).Y<=7]
            elif name=='Saddle':
                k=5.0/18
                values=roots(-k*d.X*d.Y,d.Z-k*((o.X-3)*d.Y+o.Y*d.X),o.Z-3-k*(o.X-3)*o.Y)
                values=[t for t in values if 0<=line.PointAt(t).X<=6 and -3<=line.PointAt(t).Y<=3]
            elif name=='Sphere':
                box=b.GetBoundingBox(True);center=box.Center;r=(box.Max.X-box.Min.X)/2;q=o-center
                values=roots(d*d,2*(q*d),q*q-r*r)
            if values is None:ok,ts=Intersection.CurveBrep(curve,b,1e-9,1e-9)
            else:ts=[curve.Domain.ParameterAt(t) for t in values if 0<=t<=1]
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
    name,b,p=result;n=Vector3d(p.X-11,p.Y,-27.0/49*(p.Z-3.5)) if name=='Hyperboloid' else normal_at(b,p)
    if n*line.Direction>0:n=-n
    if n*sun<=1e-9:return form,name
    hit=trace(Line(p+sun*1e-6,p+sun*1000))
    return hit is not None,name


report={'pid':EXPECTED_PID,'version':api('describe')['version'],'cases':[],'mixed':[]}
assert report['version']=='0.4.1'
try:
 for name,top,light in [('perspective',False,[-.3,-1,1]),('top',True,[-.3,-1,1]),('other-sun',False,[1,-1,2])]:
    if top:vp.SetProjection(DefinedViewportProjection.Top,'Accuracy_Top',True)
    else:
        vp.SetProjection(DefinedViewportProjection.Perspective,'Accuracy_Perspective',True)
        vp.SetCameraLocations(Point3d(11,0,2),Point3d(45,-48,36))
    vp.ZoomBoundingBox(BoundingBox(Point3d(-11,-7,-2),Point3d(34,7,10)))
    before=snapshot()
    result=api('export_shadow_psd',backend='volume',width=1024,path=os.path.join(folder,name+'.psd'),overwrite=True,toSun=light)
    assert before==snapshot()
    base=api('export_psd',width=1024,path=os.path.join(folder,'base-'+name+'.psd'),overwrite=True)
    sun=Vector3d(*light);sun.Unitize();w=result['export']['width'];h=result['export']['height']
    samples=[]
    if name=='perspective':
        # Every pixel in a fixed rectangle across the observed terminator, including
        # previously clear neighbours. No exclusion of reference shadow boundaries.
        coords=[(x,y) for y in range(215,302) for x in range(463,540)]
    else:
        geometry=next(b for label,b in refs if label=='Hyperboloid')
        points=[vp.WorldToClient(p) for p in geometry.GetBoundingBox(True).GetCorners()]
        left=max(0,int(min(p.X for p in points)*w/vp.Size.Width));right=min(w-1,int(max(p.X for p in points)*w/vp.Size.Width))
        top_edge=max(0,int(min(p.Y for p in points)*h/vp.Size.Height));bottom=min(h-1,int(max(p.Y for p in points)*h/vp.Size.Height))
        coords=[(x,y) for y in range(top_edge,bottom,2) for x in range(left,right,2)]
    for x,y in coords:
        states=[];labels=[]
        for dy,dx in [(.25,.25),(.25,.75),(.75,.25),(.75,.75)]:
            expected,label=oracle(x+dx,y+dy,w,h,sun,False);states.append(expected);labels.append(label)
        if all(label=='Hyperboloid' for label in labels):samples.append(dict(x=x,y=y,shadow=states))
    if name=='perspective':
        for x,y in [(537,241),(478,247)]:
            states=[oracle(x+dx,y+dy,w,h,sun,False)[0] for dy,dx in [(.25,.25),(.25,.75),(.75,.25),(.75,.75)]]
            report['mixed'].append(dict(x=x,y=y,shadow=states))
    report['cases'].append(dict(name=name,result=result,base=base,samples=samples,stateUnchanged=True))
    with open(os.path.join(folder,'report.json'),'w') as f:json.dump(report,f,indent=2)
 report['complete']=True
finally:
 vp.SetViewProjection(saved,True);saved.Dispose();doc.Modified=modified
 report['viewRestored']=True
 with open(os.path.join(folder,'report.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(complete=report.get('complete'),pid=EXPECTED_PID,cases=[dict(name=c['name'],samples=len(c['samples']),export=c['result']['export']) for c in report['cases']])))
