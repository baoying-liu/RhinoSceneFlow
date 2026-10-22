"""Experimental finite ground-plane projection using Rhino ProjectAlong and shared camera rasterization."""
import clr,System,Rhino,os,json
from System.Collections.Generic import List
from Rhino.Geometry import Point3d,Plane,Vector3d,Transform
clr.AddReference('RhinoSceneFlow.Plugin')
from RhinoSceneFlow.Core import Triangle,ColorGroup,Rgb,FlatRasterizer,PsdWriter,Vec3
assert System.Diagnostics.Process.GetCurrentProcess().Id==EXPECTED_PID
doc=__rhino_doc__;vp=doc.Views.ActiveView.ActiveViewport
assert all(o.Attributes.GetUserString('SceneFlowShadowResearch')=='20261022' for o in doc.Objects)
folder=os.path.join(OUTPUT_DIR,'alternatives')
with open(os.path.join(folder,'native-report.json')) as f:report=json.load(f)
assembly=next(a for a in System.AppDomain.CurrentDomain.GetAssemblies() if a.GetName().Name=='RhinoSceneFlow.Plugin')
type=assembly.GetType('RhinoSceneFlow.Plugin.SceneReader')
reader=System.Activator.CreateInstance(type,System.Array[System.Object]([doc,vp,System.Threading.CancellationToken(),False,False]))
triangles=list(type.GetMethod('Read').Invoke(reader,None));world=type.GetProperty('WorldTriangles').GetValue(reader);camera=type.GetProperty('Camera').GetValue(reader)
project=Transform.ProjectAlong(Plane(Point3d(0,0,-2),Vector3d.ZAxis),Vector3d(*[-v for v in report['toSun']]))
width=report['width'];height=report['height']
alltri=List[Triangle]();count=0
# Original geometry remains a camera occluder. Ground-shadow group 0 wins only
# coplanar ties on the receiving plane, never geometry in front of that plane.
for tri in triangles:alltri.Add(Triangle(tri.A,tri.B,tri.C,1))
def clip(poly,axis,edge,sign):
    result=[]
    if not poly:return result
    p=poly[-1];pd=sign*(getattr(p,axis)-edge)
    for q in poly:
        qd=sign*(getattr(q,axis)-edge)
        if (pd>=0)!=(qd>=0):
            t=pd/(pd-qd);result.append(Point3d(p.X+(q.X-p.X)*t,p.Y+(q.Y-p.Y)*t,p.Z+(q.Z-p.Z)*t))
        if qd>=0:result.append(q)
        p=q;pd=qd
    return result
for t in world:
    poly=[Point3d(p.X,p.Y,p.Z) for p in [t.A,t.B,t.C]]
    if max(p.Z for p in poly)<=-2+1e-7:continue
    poly=clip(poly,'Z',-2,1)
    for p in poly:p.Transform(project)
    for axis,edge,sign in [('X',-11,1),('X',34,-1),('Y',-7,1),('Y',7,-1)]:poly=clip(poly,axis,edge,sign)
    if len(poly)<3:continue
    v=[camera.Project(Vec3(p.X,p.Y,p.Z)) for p in poly]
    for i in range(1,len(v)-1):alltri.Add(Triangle(v[0],v[i],v[i+1],0));count+=1
groups=List[ColorGroup]();groups.Add(ColorGroup('Ground shadow - geometric projection',Rgb(90,90,90)));groups.Add(ColorGroup('Camera occluder',Rgb(255,255,255)))
image=FlatRasterizer.Render(width,height,groups,alltri)
# This experimental image is not a Rhino document object. Remove its white holdout
# samples after the shared depth test, preserving all four antialias sub-samples.
owners=image.GetType().GetField('owners',System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance).GetValue(image)
for i in range(owners.Length):
    if owners[i]!=0:owners[i]=-1
path=os.path.join(folder,'planar-ground.psd');PsdWriter.Save(path,image)
report['planar']={'path':path,'projectedTriangles':count,'groundZ':-2,'receiverBounds':[-11,34,-7,7],'curveReceiversSupported':False}
with open(os.path.join(folder,'native-report.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report['planar']))
